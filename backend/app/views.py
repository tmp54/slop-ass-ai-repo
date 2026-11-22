"""Build response models from ORM rows, applying role-based visibility."""

from app.models import Handoff
from app.schemas import BriefVersionOut, HandoffDetail, HandoffSummary, Status
from app.services import current_brief
from app.state_machine import Actor, State, available_events

_RECEIVER_VISIBLE = {
    State.SENDER_APPROVED,
    State.RECEIVER_RESTATED,
    State.SENDER_CONFIRMED,
    State.COMPLETED,
}


def summary(handoff: Handoff) -> HandoffSummary:
    return HandoffSummary(
        id=handoff.id,
        title=handoff.title,
        state=handoff.state,
        question_count=len(handoff.questions),
        created_at=handoff.created_at,
        updated_at=handoff.updated_at,
    )


def detail(handoff: Handoff, role: Actor) -> HandoffDetail:
    brief = current_brief(handoff)
    hidden = role == Actor.RECEIVER and State(handoff.state) not in _RECEIVER_VISIBLE
    return HandoffDetail(
        **summary(handoff).model_dump(),
        notes=handoff.notes,
        links=handoff.links,
        brief=BriefVersionOut.model_validate(brief) if brief and not hidden else None,
        questions=handoff.questions,
        restatements=handoff.restatements,
        confirmations=handoff.confirmations,
        transitions=handoff.transitions,
        available_events=available_events(State(handoff.state), role),
    )


def status(handoff: Handoff, role: Actor) -> Status:
    brief = current_brief(handoff)
    return Status(
        id=handoff.id,
        state=handoff.state,
        updated_at=handoff.updated_at,
        brief_version=brief.version if brief else None,
        question_count=len(handoff.questions),
        unanswered_question_count=sum(1 for q in handoff.questions if q.answer is None),
        restatement_count=len(handoff.restatements),
        available_events=available_events(State(handoff.state), role),
    )
