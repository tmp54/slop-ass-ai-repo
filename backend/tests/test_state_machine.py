import itertools

import pytest

from app import state_machine as sm
from app.state_machine import Action, Actor, Event, State

VALID = [
    (State.SUBMITTED, Event.DRAFT, Actor.AI, State.AI_DRAFTED),
    (State.SUBMITTED, Event.DRAFT, Actor.SENDER, State.AI_DRAFTED),
    (State.AI_DRAFTED, Event.DRAFT, Actor.SENDER, State.AI_DRAFTED),
    (State.AI_DRAFTED, Event.DRAFT, Actor.AI, State.AI_DRAFTED),
    (State.AI_DRAFTED, Event.APPROVE, Actor.SENDER, State.SENDER_APPROVED),
    (State.SENDER_APPROVED, Event.RESTATE, Actor.RECEIVER, State.RECEIVER_RESTATED),
    (State.RECEIVER_RESTATED, Event.REQUEST_REVISION, Actor.SENDER, State.SENDER_APPROVED),
    (State.RECEIVER_RESTATED, Event.CONFIRM, Actor.SENDER, State.SENDER_CONFIRMED),
    (State.SENDER_CONFIRMED, Event.COMPLETE, Actor.SENDER, State.COMPLETED),
]
TRANSITION_EVENTS = [e for e in Event if e != Event.SUBMIT]


@pytest.mark.parametrize("state,event,actor,target", VALID)
def test_valid_transitions(state, event, actor, target):
    assert sm.next_state(state, event, actor) == target


def test_every_other_combination_is_rejected():
    valid = {(s, e, a) for s, e, a, _ in VALID}
    for state, event, actor in itertools.product(State, TRANSITION_EVENTS, Actor):
        if (state, event, actor) in valid:
            continue
        with pytest.raises((sm.ForbiddenActor, sm.InvalidTransition)):
            sm.next_state(state, event, actor)


def test_wrong_actor_is_forbidden_wrong_state_is_invalid():
    with pytest.raises(sm.ForbiddenActor):
        sm.next_state(State.AI_DRAFTED, Event.APPROVE, Actor.RECEIVER)
    with pytest.raises(sm.InvalidTransition):
        sm.next_state(State.SUBMITTED, Event.APPROVE, Actor.SENDER)


@pytest.mark.parametrize("event", [e for e in TRANSITION_EVENTS if e != Event.DRAFT])
def test_ai_can_never_trigger_anything_but_draft(event):
    for state in State:
        with pytest.raises(sm.ForbiddenActor):
            sm.next_state(state, event, Actor.AI)


def test_completed_is_terminal():
    for event, actor in itertools.product(TRANSITION_EVENTS, Actor):
        with pytest.raises((sm.ForbiddenActor, sm.InvalidTransition)):
            sm.next_state(State.COMPLETED, event, actor)


def test_only_sender_can_reach_completed():
    for actor in (Actor.AI, Actor.RECEIVER):
        with pytest.raises(sm.ForbiddenActor):
            sm.next_state(State.SENDER_CONFIRMED, Event.COMPLETE, actor)


def test_actions():
    sm.check_action(State.AI_DRAFTED, Action.EDIT_BRIEF, Actor.SENDER)
    sm.check_action(State.SENDER_APPROVED, Action.ASK_QUESTION, Actor.RECEIVER)
    sm.check_action(State.RECEIVER_RESTATED, Action.ANSWER_QUESTION, Actor.SENDER)
    with pytest.raises(sm.InvalidTransition):
        sm.check_action(State.SENDER_CONFIRMED, Action.ASK_QUESTION, Actor.RECEIVER)
    with pytest.raises(sm.ForbiddenActor):
        sm.check_action(State.AI_DRAFTED, Action.EDIT_BRIEF, Actor.RECEIVER)


def test_available_events():
    assert "approve" in sm.available_events(State.AI_DRAFTED, Actor.SENDER)
    assert sm.available_events(State.AI_DRAFTED, Actor.RECEIVER) == []
    assert sm.available_events(State.COMPLETED, Actor.SENDER) == []
