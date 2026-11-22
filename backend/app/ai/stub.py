"""Canned AI pipeline so the backend runs and tests pass without an LLM."""

from app.ai.interface import BriefDraft, LinkReference


class StubPipeline:
    def draft_brief(self, notes: str, links: list[str]) -> BriefDraft:
        return BriefDraft(
            progress=f"(stub) {notes[:200]}",
            decisions=["(stub) Decision recorded from sender notes"],
            remaining_tasks=["(stub) Finish the remaining work described in the notes"],
            blockers=[],
            references=[LinkReference(url=url) for url in links],
            gaps=[f"content not fetched: {url}" for url in links] + ["(stub) No real analysis performed"],
        )

    def compare_restatement(self, brief: BriefDraft, restatement: str) -> list[str]:
        return ["(stub) Restatement was not analysed"]
