import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (register tables)
from app.db import Base, get_db, make_engine
from app.main import app

SENDER = {"X-Role": "sender"}
RECEIVER = {"X-Role": "receiver"}


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def create(client, **overrides):
    body = {"title": "Auth refactor", "notes": "Half done", "links": ["https://github.com/o/r/pull/1"]}
    return client.post("/handoffs", json={**body, **overrides}, headers=SENDER)


def advance(client, hid: int, target: str) -> None:
    """Drive a fresh (ai_drafted) handoff to `target` via valid API calls."""
    steps = [
        ("sender_approved", lambda: client.post(f"/handoffs/{hid}/approve", headers=SENDER)),
        (
            "receiver_restated",
            lambda: client.post(f"/handoffs/{hid}/restatements", json={"text": "I do X"}, headers=RECEIVER),
        ),
        ("sender_confirmed", lambda: client.post(f"/handoffs/{hid}/confirm", headers=SENDER)),
        ("completed", lambda: client.post(f"/handoffs/{hid}/complete", headers=SENDER)),
    ]
    for state, call in steps:
        response = call()
        assert response.status_code in (200, 201), response.text
        if state == target:
            return
    raise AssertionError(f"unknown target {target}")
