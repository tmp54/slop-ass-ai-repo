"""Handoff business logic. Every state change goes through `_transition`, guarded by state_machine."""

from sqlalchemy.orm import Session

from app.ai import interface as ai
from app.ai.interface import BriefDraft
from app.errors import ApiError
from app.models import BriefVersion, Confirmation, Handoff, Question, Restatement, Transition, utcnow
from app.schemas import HandoffCreate
from app.state_machine import Action, Actor, Event, State, check_action, next_state


def get_handoff(db: Session, handoff_id: int) -> Handoff:
    handoff = db.get(Handoff, handoff_id)
    if handoff is None:
        raise ApiError(404, "not_found", f"Handoff {handoff_id} not found")
    return handoff


def _transition(db: Session, handoff: Handoff, event: Event, actor: Actor, target: State) -> None:
    """Persist a state change and its audit row. Callers must have validated it with next_state."""
    now = utcnow()
    db.add(
        Transition(
            handoff_id=handoff.id,
            event=event,
            from_state=handoff.state,
            to_state=target,
            actor=actor,
            created_at=now,
        )
    )
    handoff.state = target
    handoff.updated_at = now


def _touch(handoff: Handoff) -> None:
    handoff.updated_at = utcnow()


def _add_brief(db: Session, handoff: Handoff, content: BriefDraft, source: str) -> None:
    db.add(
        BriefVersion(
            handoff_id=handoff.id,
            version=len(handoff.briefs) + 1,
            source=source,
            content=content.model_dump(mode="json"),
        )
    )
    db.flush()
    db.refresh(handoff, ["briefs"])


def current_brief(handoff: Handoff) -> BriefVersion | None:
    return handoff.briefs[-1] if handoff.briefs else None


def create_handoff(db: Session, data: HandoffCreate) -> Handoff:
    """Submit, then draft with the AI. If drafting fails the handoff stays `submitted` for a retry."""
    handoff = Handoff(
        title=data.title,
        notes=data.notes,
        links=[str(url) for url in data.links],
        state=State.SUBMITTED,
    )
    db.add(handoff)
    db.flush()
    db.add(
        Transition(
            handoff_id=handoff.id,
            event=Event.SUBMIT,
            from_state=None,
            to_state=State.SUBMITTED,
            actor=Actor.SENDER,
        )
    )
    db.commit()
    try:
        _draft(db, handoff, Actor.AI)
    except ai.AIPipelineError:
        db.rollback()
    return handoff


def _draft(db: Session, handoff: Handoff, actor: Actor) -> None:
    target = next_state(State(handoff.state), Event.DRAFT, actor)
    content = ai.draft_brief(handoff.notes, handoff.links)
    _add_brief(db, handoff, content, source="ai")
    _transition(db, handoff, Event.DRAFT, actor, target)
    db.commit()


def redraft(db: Session, handoff: Handoff, actor: Actor) -> Handoff:
    _draft(db, handoff, actor)
    return handoff


def edit_brief(db: Session, handoff: Handoff, actor: Actor, content: BriefDraft) -> Handoff:
    check_action(State(handoff.state), Action.EDIT_BRIEF, actor)
    _add_brief(db, handoff, content, source="sender")
    _touch(handoff)
    db.commit()
    return handoff


def _simple_transition(db: Session, handoff: Handoff, event: Event, actor: Actor) -> Handoff:
    target = next_state(State(handoff.state), event, actor)
    _transition(db, handoff, event, actor, target)
    db.commit()
    return handoff


def approve(db: Session, handoff: Handoff, actor: Actor) -> Handoff:
    return _simple_transition(db, handoff, Event.APPROVE, actor)


def complete(db: Session, handoff: Handoff, actor: Actor) -> Handoff:
    return _simple_transition(db, handoff, Event.COMPLETE, actor)


def restate(db: Session, handoff: Handoff, actor: Actor, text: str) -> Handoff:
    target = next_state(State(handoff.state), Event.RESTATE, actor)
    brief = current_brief(handoff)
    misunderstandings = ai.compare_restatement(BriefDraft(**brief.content), text)
    db.add(
        Restatement(
            handoff_id=handoff.id,
            brief_version=brief.version,
            text=text,
            misunderstandings=misunderstandings,
        )
    )
    _transition(db, handoff, Event.RESTATE, actor, target)
    db.commit()
    db.refresh(handoff)
    return handoff


def _review_restatement(
    db: Session, handoff: Handoff, event: Event, actor: Actor, accepted: bool, comment: str | None
) -> Handoff:
    target = next_state(State(handoff.state), event, actor)
    db.add(
        Confirmation(
            handoff_id=handoff.id,
            restatement_id=handoff.restatements[-1].id,
            accepted=accepted,
            comment=comment,
        )
    )
    _transition(db, handoff, event, actor, target)
    db.commit()
    db.refresh(handoff)
    return handoff


def request_revision(db: Session, handoff: Handoff, actor: Actor, comment: str) -> Handoff:
    return _review_restatement(db, handoff, Event.REQUEST_REVISION, actor, False, comment)


def confirm(db: Session, handoff: Handoff, actor: Actor, comment: str | None) -> Handoff:
    return _review_restatement(db, handoff, Event.CONFIRM, actor, True, comment)


def ask_question(db: Session, handoff: Handoff, actor: Actor, text: str) -> Question:
    check_action(State(handoff.state), Action.ASK_QUESTION, actor)
    question = Question(handoff_id=handoff.id, text=text)
    db.add(question)
    _touch(handoff)
    db.commit()
    return question


def answer_question(
    db: Session, handoff: Handoff, actor: Actor, question_id: int, answer: str
) -> Question:
    check_action(State(handoff.state), Action.ANSWER_QUESTION, actor)
    question = db.get(Question, question_id)
    if question is None or question.handoff_id != handoff.id:
        raise ApiError(404, "not_found", f"Question {question_id} not found")
    question.answer = answer
    question.answered_at = utcnow()
    _touch(handoff)
    db.commit()
    return question
