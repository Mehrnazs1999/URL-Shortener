
from typing import Annotated

from fastapi import APIRouter, Path, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from app.services.url_services import (
    create_short_url,
    get_original_url,
    get_url_stats,
)

router = APIRouter(tags=["URLs"])


class URLCreate(BaseModel):
    original_url: HttpUrl


ShortCode = Annotated[
    str,
    Path(
        min_length=1,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_-]+$",
    ),
]


@router.post(
    "/shorten",
    status_code=status.HTTP_201_CREATED,
)
def shorten_url(request: URLCreate):
    short_code = create_short_url(request)

    return {
        "short_code": short_code,
        "short_url": f"http://localhost:8000/{short_code}",
        "original_url": str(request.original_url),
    }


@router.get("/{short_code}")
def redirect_to_original(short_code: ShortCode):
    original_url = get_original_url(short_code)

    return RedirectResponse(
        url=original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


@router.get("/stats/{short_code}")
def find_url_stat(short_code: ShortCode):
    url_stat = get_url_stats(short_code)

    return {"url_stat": url_stat}
