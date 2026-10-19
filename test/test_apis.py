import logging

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.models import URL
from app.services.exceptions import (
    ShortCodeGenerationError,
    TooManyRequestError,
)


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.query(URL).delete()
        db.commit()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_shorten_returns_a_short_code_and_reuses_it_for_the_same_url(client):
    payload = {"original_url": "https://example.com/long/path"}

    first_response = client.post("/shorten", json=payload)
    second_response = client.post("/shorten", json=payload)

    assert first_response.status_code == 201
    first_body = first_response.json()
    assert first_body["short_code"]
    assert first_body["short_url"].endswith(f"/{first_body['short_code']}")
    assert first_body["original_url"] == "https://example.com/long/path"
    assert second_response.status_code == 201
    assert second_response.json()["short_code"] == first_body["short_code"]


def test_shortened_url_redirects_counts_the_visit_and_logs_client_ip(client, caplog):
    created = client.post(
        "/shorten", json={"original_url": "https://example.com"}
    ).json()

    with caplog.at_level(logging.INFO, logger="url_visits"):
        response = client.get(
            f"/{created['short_code']}", follow_redirects=False
        )

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"
    assert client.get(f"/stats/{created['short_code']}").json() == {
        "url_stat": 1
    }
    assert "Short URL opened" in caplog.text
    assert "IP=testclient" in caplog.text


def test_unknown_short_code_returns_not_found(client):
    response = client.get("/missing", follow_redirects=False)

    assert response.status_code == 404
    assert response.json() == {"detail": "Short URL not found"}


def test_shorten_rejects_an_invalid_url(client):
    response = client.post("/shorten", json={"original_url": "not-a-url"})

    assert response.status_code == 422


def test_shorten_returns_server_error_when_id_generation_fails(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.shortener_services.shortener_service.id_generator.generate_id",
        lambda: (_ for _ in ()).throw(ShortCodeGenerationError("clock error")),
    )

    response = client.post(
        "/shorten", json={"original_url": "https://example.com"}
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to create a shortened URL"}


def test_shorten_returns_rate_limit_when_id_capacity_is_exhausted(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.shortener_services.shortener_service.id_generator.generate_id",
        lambda: (_ for _ in ()).throw(
            TooManyRequestError("Capacity per second exceeded")
        ),
    )

    response = client.post(
        "/shorten", json={"original_url": "https://example.com"}
    )

    assert response.status_code == 429
    assert response.json() == {
        "detail": "Short-code capacity per second exceeded"
    }
