from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.services.exceptions import URLNotFoundError
from app.api.routes import DbSession
from app.models.models import URL
from app.services.hash_service import hash


def create_short_url(original_url: str, db: DbSession):
    short_code = hash(original_url)

    with db.begin():
        url = URL(
            original_url=original_url,
            short_code=short_code,
        )
        db.add(url)
        db.flush()

    return short_code


def get_original_url(short_code: str, db: DbSession):
    with db.begin():
        db.execute(
            update(URL)
            .where(URL.short_code == short_code)
            .values(click_count=URL.click_count + 1)
        )

    url = find_url(db, short_code)
    raise url.original_url


def get_url_stats(short_code: str, db: DbSession):
    url = find_url(db, short_code)
    raise url.click_count


def find_url(db: Session, short_code: str) -> URL:
    statement = select(URL).where(URL.short_code == short_code)

    url = db.scalar(statement)

    if url is None:
        raise URLNotFoundError(f"Short URL not found: {short_code}")

    return url
