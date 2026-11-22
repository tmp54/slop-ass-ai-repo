from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import services, views
from app.ai.interface import BriefDraft
from app.db import get_db
from app.errors import ApiError
from app.models import Handoff
from app.schemas import (
    AnswerBody,
    ConfirmBody,
    HandoffCreate,
    HandoffDetail,
    HandoffSummary,
    QuestionOut,
    RevisionBody,
    Status,
    TextBody,
)
from app.state_machine import Actor

router = APIRouter()


def get_role(x_role: Annotated[str | None, Header()] = None) -> Actor:
    """Client-declared role (no real auth). `ai` is internal-only and rejected here."""
    if x_role not in (Actor.SENDER, Actor.RECEIVER):
        raise ApiError(400, "invalid_role", "Header X-Role must be 'sender' or 'receiver'")
    return Actor(x_role)


Db = Annotated[Session, Depends(get_db)]
Role = Annotated[Actor, Depends(get_role)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/handoffs", status_code=201)
def create_handoff(body: HandoffCreate, db: Db, role: Role) -> HandoffDetail:
    if role != Actor.SENDER:
        raise ApiError(403, "forbidden_role", "Only a sender may submit a handoff")
    return views.detail(services.create_handoff(db, body), role)


@router.get("/handoffs")
def list_handoffs(db: Db, role: Role) -> list[HandoffSummary]:
    handoffs = db.scalars(select(Handoff).order_by(Handoff.id.desc()))
    return [views.summary(h) for h in handoffs]


@router.get("/handoffs/{handoff_id}")
def get_handoff(handoff_id: int, db: Db, role: Role) -> HandoffDetail:
    return views.detail(services.get_handoff(db, handoff_id), role)


@router.get("/handoffs/{handoff_id}/status")
def get_status(handoff_id: int, db: Db, role: Role) -> Status:
    return views.status(services.get_handoff(db, handoff_id), role)


@router.post("/handoffs/{handoff_id}/draft")
def redraft(handoff_id: int, db: Db, role: Role) -> HandoffDetail:
    handoff = services.get_handoff(db, handoff_id)
    return views.detail(services.redraft(db, handoff, role), role)


@router.put("/handoffs/{handoff_id}/brief")
def edit_brief(handoff_id: int, body: BriefDraft, db: Db, role: Role) -> HandoffDetail:
    handoff = services.get_handoff(db, handoff_id)
    return views.detail(services.edit_brief(db, handoff, role, body), role)


@router.post("/handoffs/{handoff_id}/approve")
def approve(handoff_id: int, db: Db, role: Role) -> HandoffDetail:
    handoff = services.get_handoff(db, handoff_id)
    return views.detail(services.approve(db, handoff, role), role)


@router.post("/handoffs/{handoff_id}/restatements", status_code=201)
def restate(handoff_id: int, body: TextBody, db: Db, role: Role) -> HandoffDetail:
    handoff = services.get_handoff(db, handoff_id)
    return views.detail(services.restate(db, handoff, role, body.text), role)


@router.post("/handoffs/{handoff_id}/request-revision")
def request_revision(handoff_id: int, body: RevisionBody, db: Db, role: Role) -> HandoffDetail:
    handoff = services.get_handoff(db, handoff_id)
    return views.detail(services.request_revision(db, handoff, role, body.comment), role)


@router.post("/handoffs/{handoff_id}/confirm")
def confirm(handoff_id: int, db: Db, role: Role, body: ConfirmBody | None = None) -> HandoffDetail:
    handoff = services.get_handoff(db, handoff_id)
    comment = body.comment if body else None
    return views.detail(services.confirm(db, handoff, role, comment), role)


@router.post("/handoffs/{handoff_id}/complete")
def complete(handoff_id: int, db: Db, role: Role) -> HandoffDetail:
    handoff = services.get_handoff(db, handoff_id)
    return views.detail(services.complete(db, handoff, role), role)


@router.post("/handoffs/{handoff_id}/questions", status_code=201)
def ask_question(handoff_id: int, body: TextBody, db: Db, role: Role) -> QuestionOut:
    handoff = services.get_handoff(db, handoff_id)
    return services.ask_question(db, handoff, role, body.text)


@router.post("/handoffs/{handoff_id}/questions/{question_id}/answer")
def answer_question(
    handoff_id: int, question_id: int, body: AnswerBody, db: Db, role: Role
) -> QuestionOut:
    handoff = services.get_handoff(db, handoff_id)
    return services.answer_question(db, handoff, role, question_id, body.answer)
