"""Real AI pipeline (Anthropic SDK). Enable with AI_PIPELINE=app.ai.pipeline:Pipeline.

The pipeline only returns data. It never changes handoff state and never declares anything verified or complete.
"""

import logging
import re
from collections.abc import Callable
from typing import Any

import anthropic
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.ai.github import GitHubContent, fetch_github_content
from app.ai.interface import AIPipelineError, BriefDraft, LinkReference
from app.ai.prompts import COMPARE_RESTATEMENT_VERSION, DRAFT_BRIEF_VERSION, load_prompt
from app.config import get_settings

log = logging.getLogger(__name__)

MAX_QUESTIONS = 10


class AISettings(BaseSettings):
    """Extra AI settings read from env / .env (kept here so config.py stays untouched)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_model: str = "claude-sonnet-5-5"
    anthropic_timeout_seconds: float = 60.0
    anthropic_max_tokens: int = 4096


class ReferenceNote(BaseModel):
    url: str
    note: str


class DraftOutput(BaseModel):
    """What the LLM must return. References/fetch gaps are merged in by code."""

    progress: str
    decisions: list[str] = Field(default_factory=list)
    remaining_tasks: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    reference_notes: list[ReferenceNote] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class ComparisonOutput(BaseModel):
    misunderstandings: list[str] = Field(default_factory=list)


def _clean(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _fence(text: str, tag: str) -> str:
    """Neutralise any attempt to close/open our data tags from inside untrusted text."""
    return re.sub(rf"</?\s*{re.escape(tag)}[^>]*>", "[tag removed]", text, flags=re.IGNORECASE)


def _render_github(content: GitHubContent) -> str:
    parts = [f"Type: {content.kind}", f"Title: {content.title}", f"Description:\n{content.body or '(empty)'}"]
    if content.comments:
        parts.append("Comments:\n" + "\n---\n".join(content.comments))
    if content.files:
        parts.append("Changed files:\n" + "\n".join(content.files))
    if content.patches:
        parts.append(
            "Truncated diff snippets:\n" + "\n".join(f"## {name}\n{patch}" for name, patch in content.patches.items())
        )
    return "\n\n".join(parts)


class Pipeline:
    """Implements `AIPipeline`. `client` and `fetcher` are injectable for tests."""

    def __init__(
        self,
        client: Any | None = None,
        fetcher: Callable[[str, str], GitHubContent | None] | None = None,
        model: str | None = None,
    ) -> None:
        self._client = client
        self._fetcher = fetcher or fetch_github_content
        ai = AISettings()
        self.model = model or ai.anthropic_model
        self._timeout = ai.anthropic_timeout_seconds
        self._max_tokens = ai.anthropic_max_tokens

    # -- public API -------------------------------------------------------------------------

    def draft_brief(self, notes: str, links: list[str]) -> BriefDraft:
        token = get_settings().github_token
        fetched: dict[str, GitHubContent] = {}
        fetch_gaps: list[str] = []
        for url in links:
            content = self._safe_fetch(url, token)
            if content is None:
                fetch_gaps.append(f"content not fetched: {url}")
            else:
                fetched[url] = content

        sections = [f"<sender_notes>\n{_fence(notes, 'sender_notes')}\n</sender_notes>"]
        for url, content in fetched.items():
            body = _fence(_render_github(content), "untrusted_github_content")
            sections.append(f'<untrusted_github_content url="{url}">\n{body}\n</untrusted_github_content>')
        if fetch_gaps:
            sections.append("Links whose content could not be fetched:\n" + "\n".join(links_unfetched(fetch_gaps)))
        user_msg = "\n\n".join(sections)

        out = self._call_structured(
            system=load_prompt(DRAFT_BRIEF_VERSION),
            user=user_msg,
            tool_name="submit_brief",
            tool_description="Submit the structured handoff brief.",
            model_cls=DraftOutput,
        )
        if not out.progress.strip():
            raise AIPipelineError("model returned an empty progress section")

        notes_by_url = {n.url: n.note.strip() for n in out.reference_notes if n.note.strip()}
        references = [
            LinkReference(
                url=url,
                title=fetched[url].title if url in fetched else None,
                note=notes_by_url.get(url),
            )
            for url in dict.fromkeys(links)
        ]
        gaps = _clean(out.gaps) + [g for g in fetch_gaps if g not in out.gaps]
        return BriefDraft(
            progress=out.progress.strip(),
            decisions=_clean(out.decisions),
            remaining_tasks=_clean(out.remaining_tasks),
            blockers=_clean(out.blockers),
            references=references,
            gaps=gaps,
        )

    def compare_restatement(self, brief: BriefDraft, restatement: str) -> list[str]:
        user_msg = (
            f"<brief>\n{_fence(brief.model_dump_json(indent=2), 'brief')}\n</brief>\n\n"
            f"<restatement>\n{_fence(restatement, 'restatement')}\n</restatement>"
        )
        out = self._call_structured(
            system=load_prompt(COMPARE_RESTATEMENT_VERSION),
            user=user_msg,
            tool_name="submit_comparison",
            tool_description="Submit possible misunderstandings or questions for the sender.",
            model_cls=ComparisonOutput,
        )
        return _clean(out.misunderstandings)[:MAX_QUESTIONS]

    # -- internals --------------------------------------------------------------------------

    def _safe_fetch(self, url: str, token: str) -> GitHubContent | None:
        try:
            return self._fetcher(url, token)
        except Exception:  # fetch failures are gaps, never exceptions
            return None

    def _get_client(self) -> Any:
        if self._client is None:
            key = get_settings().anthropic_api_key
            if not key:
                raise AIPipelineError("ANTHROPIC_API_KEY is not set")
            self._client = anthropic.Anthropic(api_key=key, timeout=self._timeout)
        return self._client

    def _call_structured[T: BaseModel](
        self, *, system: str, user: str, tool_name: str, tool_description: str, model_cls: type[T]
    ) -> T:
        """Force a single tool call whose input is validated by Pydantic. One retry on malformed output."""
        client = self._get_client()
        tool = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": model_cls.model_json_schema(),
        }
        last_error = "unknown"
        for attempt in range(2):
            try:
                resp = client.messages.create(
                    model=self.model,
                    max_tokens=self._max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                    tools=[tool],
                    tool_choice={"type": "tool", "name": tool_name},
                )
            except anthropic.APIError as exc:  # includes timeouts and connection errors
                raise AIPipelineError(f"LLM call failed: {type(exc).__name__}") from exc
            block = next(
                (b for b in resp.content if getattr(b, "type", None) == "tool_use" and b.name == tool_name), None
            )
            if block is None:
                last_error = "no structured output returned"
            else:
                try:
                    return model_cls.model_validate(block.input)
                except ValidationError as exc:
                    last_error = f"output failed schema validation ({exc.error_count()} errors)"
            log.warning("AI output malformed (attempt %d): %s", attempt + 1, last_error)
        raise AIPipelineError(f"malformed LLM output after retry: {last_error}")


def links_unfetched(gaps: list[str]) -> list[str]:
    return [g.removeprefix("content not fetched: ") for g in gaps]
