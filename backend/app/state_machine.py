"""Handoff lifecycle rules. Pure logic: no database, no HTTP. See docs/state-machine.md."""

from dataclasses import dataclass
from enum import StrEnum


class State(StrEnum):
    SUBMITTED = "submitted"
    AI_DRAFTED = "ai_drafted"
    SENDER_APPROVED = "sender_approved"
    RECEIVER_RESTATED = "receiver_restated"
    SENDER_CONFIRMED = "sender_confirmed"
    COMPLETED = "completed"


class Actor(StrEnum):
    SENDER = "sender"
    RECEIVER = "receiver"
    AI = "ai"


class Event(StrEnum):
    SUBMIT = "submit"
    DRAFT = "draft"
    APPROVE = "approve"
    RESTATE = "restate"
    REQUEST_REVISION = "request_revision"
    CONFIRM = "confirm"
    COMPLETE = "complete"


class Action(StrEnum):
    """Operations that are guarded like events but do not change state."""

    EDIT_BRIEF = "edit_brief"
    ASK_QUESTION = "ask_question"
    ANSWER_QUESTION = "answer_question"


class ForbiddenActor(Exception):
    """The actor may never perform this operation."""


class InvalidTransition(Exception):
    """The handoff is in a state that does not allow this operation."""


@dataclass(frozen=True)
class Rule:
    sources: frozenset[State]
    actors: frozenset[Actor]
    target: State | None = None  # None for non-transition actions


def _rule(sources: set[State], actors: set[Actor], target: State | None = None) -> Rule:
    return Rule(frozenset(sources), frozenset(actors), target)


_QA_STATES = {State.SENDER_APPROVED, State.RECEIVER_RESTATED}

# The AI actor appears only on DRAFT. It can never approve, confirm or complete.
TRANSITIONS: dict[Event, Rule] = {
    Event.DRAFT: _rule(
        {State.SUBMITTED, State.AI_DRAFTED}, {Actor.AI, Actor.SENDER}, State.AI_DRAFTED
    ),
    Event.APPROVE: _rule({State.AI_DRAFTED}, {Actor.SENDER}, State.SENDER_APPROVED),
    Event.RESTATE: _rule({State.SENDER_APPROVED}, {Actor.RECEIVER}, State.RECEIVER_RESTATED),
    Event.REQUEST_REVISION: _rule(
        {State.RECEIVER_RESTATED}, {Actor.SENDER}, State.SENDER_APPROVED
    ),
    Event.CONFIRM: _rule({State.RECEIVER_RESTATED}, {Actor.SENDER}, State.SENDER_CONFIRMED),
    Event.COMPLETE: _rule({State.SENDER_CONFIRMED}, {Actor.SENDER}, State.COMPLETED),
}

ACTIONS: dict[Action, Rule] = {
    Action.EDIT_BRIEF: _rule({State.AI_DRAFTED}, {Actor.SENDER}),
    Action.ASK_QUESTION: _rule(_QA_STATES, {Actor.RECEIVER}),
    Action.ANSWER_QUESTION: _rule(_QA_STATES, {Actor.SENDER}),
}


def _check(rule: Rule, name: str, state: State, actor: Actor) -> None:
    """Actor guard first (403), then state guard (409)."""
    if actor not in rule.actors:
        raise ForbiddenActor(f"Role '{actor}' may not perform '{name}'")
    if state not in rule.sources:
        raise InvalidTransition(f"Cannot '{name}' while handoff is '{state}'")


def next_state(state: State, event: Event, actor: Actor) -> State:
    """Return the state after `event`, or raise if the actor or state is not allowed."""
    rule = TRANSITIONS[event]
    _check(rule, event, state, actor)
    assert rule.target is not None
    return rule.target


def check_action(state: State, action: Action, actor: Actor) -> None:
    _check(ACTIONS[action], action, state, actor)


def available_events(state: State, actor: Actor) -> list[str]:
    """Events and actions `actor` may trigger right now (for UI buttons)."""
    rules = {**TRANSITIONS, **ACTIONS}
    return [
        str(name)
        for name, rule in rules.items()
        if actor in rule.actors and state in rule.sources
    ]
