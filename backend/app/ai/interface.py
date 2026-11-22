"""Contract between the backend and the AI pipeline. See docs/api-contract.md.

The backend calls only `draft_brief` and `compare_restatement` from this module. They delegate to
the class named by the AI_PIPELINE setting (`module:Class`). The AI never changes handoff state.
"""

from functools import lru_cache
from importlib import import_module
from typing import Protocol

from pydantic import BaseModel, Field

from app.config import get_settings


class LinkReference(BaseModel):
    url: str
    title: str | None = None
    note: str | None = None


class BriefDraft(BaseModel):
    """Structured handoff brief. Also the API's `BriefContent`."""

    progress: str
    decisions: list[str] = Field(default_factory=list)
    remaining_tasks: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    references: list[LinkReference] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)  # missing details, e.g. "content not fetched: <url>"


class AIPipelineError(Exception):
    """Raise for any LLM or GitHub failure; the backend maps it to HTTP 502."""


class AIPipeline(Protocol):
    def draft_brief(self, notes: str, links: list[str]) -> BriefDraft:
        """Fetch link content (GitHub) and organise notes into a brief, listing gaps."""

    def compare_restatement(self, brief: BriefDraft, restatement: str) -> list[str]:
        """Return possible misunderstandings in the receiver's restatement (empty if none)."""


@lru_cache
def get_pipeline() -> AIPipeline:
    module_name, _, class_name = get_settings().ai_pipeline.partition(":")
    return getattr(import_module(module_name), class_name)()


def draft_brief(notes: str, links: list[str]) -> BriefDraft:
    return get_pipeline().draft_brief(notes, links)


def compare_restatement(brief: BriefDraft, restatement: str) -> list[str]:
    return get_pipeline().compare_restatement(brief, restatement)
