import pytest

from app.database import Base, SessionLocal, engine
from app.models.models import URL
from app.services.exceptions import URLNotFoundError
from app.services.url_services import (
    create_short_url,
    find_url,
    get_original_url,
    get_url_stats,
)


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.query(URL).delete()
        db.commit()


def test_create_short_url_persists_a_url_and_reuses_an_existing_code(monkeypatch):
    monkeypatch.setattr(
        "app.services.url_services.generate_short_code",
        lambda: "abc123",
    )

    with SessionLocal() as db:
        assert create_short_url("https://example.com", db) == "abc123"
        assert create_short_url("https://example.com", db) == "abc123"

        saved_url = find_url(db, "abc123")

    assert saved_url.original_url == "https://example.com"


def test_get_original_url_returns_destination_and_increments_click_count():
    with SessionLocal() as db:
        db.add(URL(original_url="https://example.com", short_code="abc123"))
        db.commit()

        assert get_original_url("abc123", db) == "https://example.com"
        assert get_url_stats("abc123", db) == 1


def test_missing_short_code_raises_domain_error():
    with SessionLocal() as db:
        with pytest.raises(URLNotFoundError, match="Short URL not found"):
            find_url(db, "missing")

        with pytest.raises(URLNotFoundError):
            get_original_url("missing", db)

        with pytest.raises(URLNotFoundError):
            get_url_stats("missing", db)
