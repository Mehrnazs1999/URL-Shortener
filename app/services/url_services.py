from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.services.exceptions import URLNotFoundError
from app.models.models import URL
from app.services.shortener_services.shortener_service import generate_short_code


def create_short_url(original_url: str, db: Session) -> str:
    statement = select(URL).where(URL.original_url == original_url)
    existing_url = db.scalar(statement)

    if existing_url is not None:
        return existing_url.short_code

    short_code = generate_short_code()
    url = URL(
        original_url=original_url,
        short_code=short_code,
    )
    db.add(url)
    db.commit()

    return short_code


def get_original_url(short_code: str, db: Session) -> str:
    url = find_url(db, short_code)

    db.execute(
        update(URL)
        .where(URL.short_code == short_code)
        .values(click_count=URL.click_count + 1)
    )
    db.commit()

    return url.original_url


def get_url_stats(short_code: str, db: Session) -> int:
    url = find_url(db, short_code)
    return url.click_count


def find_url(db: Session, short_code: str) -> URL:
    statement = select(URL).where(URL.short_code == short_code)

    url = db.scalar(statement)

    if url is None:
        raise URLNotFoundError(f"Short URL not found: {short_code}")

    return url
