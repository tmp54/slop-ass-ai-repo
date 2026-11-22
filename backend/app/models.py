"""SQLAlchemy ORM models. Timestamps are naive UTC (SQLite has no timezone support)."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Handoff(Base):
    __tablename__ = "handoffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text)
    links: Mapped[list[str]] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    briefs: Mapped[list["BriefVersion"]] = relationship(order_by="BriefVersion.version")
    transitions: Mapped[list["Transition"]] = relationship(order_by="Transition.id")
    restatements: Mapped[list["Restatement"]] = relationship(order_by="Restatement.id")
    questions: Mapped[list["Question"]] = relationship(order_by="Question.id")
    confirmations: Mapped[list["Confirmation"]] = relationship(order_by="Confirmation.id")


class BriefVersion(Base):
    __tablename__ = "brief_versions"
    __table_args__ = (UniqueConstraint("handoff_id", "version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    handoff_id: Mapped[int] = mapped_column(ForeignKey("handoffs.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(16))  # "ai" or "sender"
    content: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Transition(Base):
    """Audit log: one row per state change, with who triggered it and when."""

    __tablename__ = "transitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    handoff_id: Mapped[int] = mapped_column(ForeignKey("handoffs.id"), index=True)
    event: Mapped[str] = mapped_column(String(32))
    from_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_state: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Restatement(Base):
    __tablename__ = "restatements"

    id: Mapped[int] = mapped_column(primary_key=True)
    handoff_id: Mapped[int] = mapped_column(ForeignKey("handoffs.id"), index=True)
    brief_version: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    misunderstandings: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Question(Base):
    """Receiver clarification question. The row count per handoff is an evaluation metric."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    handoff_id: Mapped[int] = mapped_column(ForeignKey("handoffs.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Confirmation(Base):
    """Sender's verdict on a restatement: accepted (confirm) or rejected (request_revision)."""

    __tablename__ = "confirmations"

    id: Mapped[int] = mapped_column(primary_key=True)
    handoff_id: Mapped[int] = mapped_column(ForeignKey("handoffs.id"), index=True)
    restatement_id: Mapped[int] = mapped_column(ForeignKey("restatements.id"))
    accepted: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
