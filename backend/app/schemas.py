"""Pydantic request and response models (the API contract; see docs/api-contract.md)."""

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from app.ai.interface import BriefDraft, LinkReference
from app.state_machine import Actor, State

__all__ = ["BriefContent", "Reference"]

BriefContent = BriefDraft
Reference = LinkReference


def _to_utc_z(value: datetime) -> str:
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[datetime, PlainSerializer(_to_utc_z, return_type=str)]


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HandoffCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = Field(min_length=1, max_length=20000)
    links: list[AnyHttpUrl] = Field(default_factory=list, max_length=20)

    @field_validator("title", "notes")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class TextBody(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class AnswerBody(BaseModel):
    answer: str = Field(min_length=1, max_length=10000)


class RevisionBody(BaseModel):
    comment: str = Field(min_length=1, max_length=10000)


class ConfirmBody(BaseModel):
    comment: str | None = Field(default=None, max_length=10000)


class BriefVersionOut(_Out):
    version: int
    source: Literal["ai", "sender"]
    created_at: UtcDatetime
    content: BriefContent


class QuestionOut(_Out):
    id: int
    text: str
    answer: str | None
    created_at: UtcDatetime
    answered_at: UtcDatetime | None


class RestatementOut(_Out):
    id: int
    brief_version: int
    text: str
    misunderstandings: list[str]
    created_at: UtcDatetime


class ConfirmationOut(_Out):
    id: int
    restatement_id: int
    accepted: bool
    comment: str | None
    created_at: UtcDatetime


class TransitionOut(_Out):
    event: str
    from_state: str | None
    to_state: str
    actor: Actor
    created_at: UtcDatetime


class HandoffSummary(BaseModel):
    id: int
    title: str
    state: State
    question_count: int
    created_at: UtcDatetime
    updated_at: UtcDatetime


class HandoffDetail(HandoffSummary):
    notes: str
    links: list[str]
    brief: BriefVersionOut | None
    questions: list[QuestionOut]
    restatements: list[RestatementOut]
    confirmations: list[ConfirmationOut]
    transitions: list[TransitionOut]
    available_events: list[str]


class Status(BaseModel):
    id: int
    state: State
    updated_at: UtcDatetime
    brief_version: int | None
    question_count: int
    unanswered_question_count: int
    restatement_count: int
    available_events: list[str]
