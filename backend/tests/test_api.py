import pytest

from app.ai import interface
from app.ai.interface import AIPipelineError
from tests.conftest import RECEIVER, SENDER, advance, create


def get(client, hid, role=SENDER):
    return client.get(f"/handoffs/{hid}", headers=role).json()


def test_submit_creates_ai_drafted_handoff_with_audit_trail(client):
    response = create(client)
    assert response.status_code == 201
    body = response.json()
    assert body["state"] == "ai_drafted"
    assert body["brief"]["version"] == 1 and body["brief"]["source"] == "ai"
    assert body["links"] == ["https://github.com/o/r/pull/1"]
    assert [(t["event"], t["actor"], t["to_state"]) for t in body["transitions"]] == [
        ("submit", "sender", "submitted"),
        ("draft", "ai", "ai_drafted"),
    ]
    assert all(t["created_at"].endswith("Z") for t in body["transitions"])


def test_ai_failure_on_submit_leaves_submitted_and_retry_works(client, monkeypatch):
    def boom(notes, links):
        raise AIPipelineError("down")

    monkeypatch.setattr(interface, "draft_brief", boom)
    body = create(client).json()
    assert body["state"] == "submitted" and body["brief"] is None
    monkeypatch.undo()
    retry = client.post(f"/handoffs/{body['id']}/draft", headers=SENDER)
    assert retry.json()["state"] == "ai_drafted"
    assert retry.json()["transitions"][-1]["actor"] == "sender"


def test_full_happy_path(client):
    hid = create(client).json()["id"]
    assert client.post(f"/handoffs/{hid}/approve", headers=SENDER).json()["state"] == "sender_approved"
    restated = client.post(f"/handoffs/{hid}/restatements", json={"text": "Next: finish X"}, headers=RECEIVER)
    assert restated.status_code == 201
    assert restated.json()["restatements"][0]["misunderstandings"]
    confirmed = client.post(f"/handoffs/{hid}/confirm", json={"comment": "good"}, headers=SENDER).json()
    assert confirmed["state"] == "sender_confirmed"
    done = client.post(f"/handoffs/{hid}/complete", headers=SENDER).json()
    assert done["state"] == "completed"
    assert [t["to_state"] for t in done["transitions"]] == [
        "submitted", "ai_drafted", "sender_approved", "receiver_restated", "sender_confirmed", "completed",
    ]
    assert done["confirmations"][0]["accepted"] is True


def test_confirm_without_body(client):
    hid = create(client).json()["id"]
    advance(client, hid, "receiver_restated")
    assert client.post(f"/handoffs/{hid}/confirm", headers=SENDER).status_code == 200


def test_request_revision_loops_back_and_allows_new_restatement(client):
    hid = create(client).json()["id"]
    advance(client, hid, "receiver_restated")
    r = client.post(f"/handoffs/{hid}/request-revision", json={"comment": "wrong"}, headers=SENDER)
    assert r.json()["state"] == "sender_approved"
    assert r.json()["confirmations"][0] == {**r.json()["confirmations"][0], "accepted": False, "comment": "wrong"}
    again = client.post(f"/handoffs/{hid}/restatements", json={"text": "v2"}, headers=RECEIVER)
    assert again.json()["state"] == "receiver_restated"
    assert len(again.json()["restatements"]) == 2


def test_request_revision_requires_comment(client):
    hid = create(client).json()["id"]
    advance(client, hid, "receiver_restated")
    r = client.post(f"/handoffs/{hid}/request-revision", json={}, headers=SENDER)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


# (path, role, body, states in which it is invalid)
INVALID_STATE_CALLS = [
    ("approve", SENDER, None, ["sender_approved", "receiver_restated", "sender_confirmed", "completed"]),
    ("restatements", RECEIVER, {"text": "x"}, ["ai_drafted", "receiver_restated", "sender_confirmed", "completed"]),
    ("request-revision", SENDER, {"comment": "c"}, ["ai_drafted", "sender_approved", "sender_confirmed", "completed"]),
    ("confirm", SENDER, None, ["ai_drafted", "sender_approved", "sender_confirmed", "completed"]),
    ("complete", SENDER, None, ["ai_drafted", "sender_approved", "receiver_restated", "completed"]),
    ("draft", SENDER, None, ["sender_approved", "receiver_restated", "sender_confirmed", "completed"]),
]
STATE_ORDER = ["ai_drafted", "sender_approved", "receiver_restated", "sender_confirmed", "completed"]


@pytest.mark.parametrize("path,role,body,states", INVALID_STATE_CALLS)
def test_invalid_state_gives_409_and_changes_nothing(client, path, role, body, states):
    for state in states:
        hid = create(client).json()["id"]
        if state != "ai_drafted":
            advance(client, hid, state)
        before = get(client, hid)
        r = client.post(f"/handoffs/{hid}/{path}", json=body, headers=role)
        assert r.status_code == 409, (path, state, r.text)
        assert r.json()["error"]["code"] == "invalid_transition"
        assert get(client, hid) == before


@pytest.mark.parametrize(
    "path,wrong_role,body,state",
    [
        ("approve", RECEIVER, None, "ai_drafted"),
        ("restatements", SENDER, {"text": "x"}, "sender_approved"),
        ("request-revision", RECEIVER, {"comment": "c"}, "receiver_restated"),
        ("confirm", RECEIVER, None, "receiver_restated"),
        ("complete", RECEIVER, None, "sender_confirmed"),
        ("draft", RECEIVER, None, "ai_drafted"),
    ],
)
def test_wrong_role_gives_403(client, path, wrong_role, body, state):
    hid = create(client).json()["id"]
    if state != "ai_drafted":
        advance(client, hid, state)
    r = client.post(f"/handoffs/{hid}/{path}", json=body, headers=wrong_role)
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden_role"


def test_ai_role_header_is_rejected_everywhere(client):
    hid = create(client).json()["id"]
    for method, path in [("post", "approve"), ("post", "complete"), ("get", "status")]:
        r = getattr(client, method)(f"/handoffs/{hid}/{path}", headers={"X-Role": "ai"})
        assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_role"


def test_missing_role_header(client):
    r = client.get("/handoffs")
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_role"


def test_receiver_cannot_submit(client):
    r = client.post("/handoffs", json={"title": "t", "notes": "n"}, headers=RECEIVER)
    assert r.status_code == 403


def test_receiver_cannot_see_brief_before_approval(client):
    hid = create(client).json()["id"]
    assert get(client, hid, RECEIVER)["brief"] is None
    assert get(client, hid, SENDER)["brief"] is not None
    advance(client, hid, "sender_approved")
    assert get(client, hid, RECEIVER)["brief"] is not None


def test_edit_brief_creates_new_version_only_while_drafted(client):
    hid = create(client).json()["id"]
    content = {"progress": "edited", "decisions": ["d"], "remaining_tasks": ["t"]}
    r = client.put(f"/handoffs/{hid}/brief", json=content, headers=SENDER)
    assert r.status_code == 200
    assert r.json()["brief"]["version"] == 2 and r.json()["brief"]["source"] == "sender"
    assert r.json()["state"] == "ai_drafted"
    assert client.put(f"/handoffs/{hid}/brief", json=content, headers=RECEIVER).status_code == 403
    advance(client, hid, "sender_approved")
    assert client.put(f"/handoffs/{hid}/brief", json=content, headers=SENDER).status_code == 409


def test_restatement_records_brief_version_and_ai_failure_changes_nothing(client, monkeypatch):
    hid = create(client).json()["id"]
    client.put(f"/handoffs/{hid}/brief", json={"progress": "p"}, headers=SENDER)
    client.post(f"/handoffs/{hid}/approve", headers=SENDER)
    monkeypatch.setattr(interface, "compare_restatement", lambda b, t: (_ for _ in ()).throw(AIPipelineError("x")))
    r = client.post(f"/handoffs/{hid}/restatements", json={"text": "t"}, headers=RECEIVER)
    assert r.status_code == 502 and r.json()["error"]["code"] == "ai_unavailable"
    assert get(client, hid)["state"] == "sender_approved"
    monkeypatch.undo()
    ok = client.post(f"/handoffs/{hid}/restatements", json={"text": "t"}, headers=RECEIVER)
    assert ok.json()["restatements"][0]["brief_version"] == 2


def test_questions_are_counted_and_answerable(client):
    hid = create(client).json()["id"]
    assert client.post(f"/handoffs/{hid}/questions", json={"text": "q"}, headers=RECEIVER).status_code == 409
    advance(client, hid, "sender_approved")
    q1 = client.post(f"/handoffs/{hid}/questions", json={"text": "q1"}, headers=RECEIVER)
    client.post(f"/handoffs/{hid}/questions", json={"text": "q2"}, headers=RECEIVER)
    assert q1.status_code == 201 and q1.json()["answer"] is None
    assert client.post(f"/handoffs/{hid}/questions", json={"text": "q"}, headers=SENDER).status_code == 403

    status = client.get(f"/handoffs/{hid}/status", headers=SENDER).json()
    assert status["question_count"] == 2 and status["unanswered_question_count"] == 2

    qid = q1.json()["id"]
    answered = client.post(f"/handoffs/{hid}/questions/{qid}/answer", json={"answer": "a"}, headers=SENDER)
    assert answered.status_code == 200 and answered.json()["answered_at"].endswith("Z")
    assert client.post(f"/handoffs/{hid}/questions/{qid}/answer", json={"answer": "a"}, headers=RECEIVER).status_code == 403
    assert client.post(f"/handoffs/{hid}/questions/999/answer", json={"answer": "a"}, headers=SENDER).status_code == 404
    status = client.get(f"/handoffs/{hid}/status", headers=SENDER).json()
    assert status["unanswered_question_count"] == 1
    assert get(client, hid)["question_count"] == 2


def test_questions_closed_after_confirmation(client):
    hid = create(client).json()["id"]
    advance(client, hid, "sender_confirmed")
    r = client.post(f"/handoffs/{hid}/questions", json={"text": "q"}, headers=RECEIVER)
    assert r.status_code == 409


def test_status_endpoint(client):
    hid = create(client).json()["id"]
    status = client.get(f"/handoffs/{hid}/status", headers=SENDER).json()
    assert status["state"] == "ai_drafted" and status["brief_version"] == 1
    assert "approve" in status["available_events"]
    assert client.get(f"/handoffs/{hid}/status", headers=RECEIVER).json()["available_events"] == []
    assert client.get("/handoffs/999/status", headers=SENDER).status_code == 404


def test_list_handoffs_newest_first(client):
    first = create(client, title="one").json()["id"]
    second = create(client, title="two").json()["id"]
    ids = [h["id"] for h in client.get("/handoffs", headers=RECEIVER).json()]
    assert ids == [second, first]


@pytest.mark.parametrize(
    "body",
    [
        {"title": "", "notes": "n"},
        {"title": "t", "notes": "   "},
        {"title": "t", "notes": "n", "links": ["not a url"]},
        {"title": "t", "notes": "n", "links": ["https://x.io"] * 21},
        {"notes": "n"},
    ],
)
def test_submit_validation(client, body):
    r = client.post("/handoffs", json=body, headers=SENDER)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_not_found_uses_error_shape(client):
    r = client.get("/handoffs/42", headers=SENDER)
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_cors_allows_vite_dev_server(client):
    r = client.options(
        "/handoffs",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "x-role"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
