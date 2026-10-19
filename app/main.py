import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import router
from app.services.exceptions import (
    ShortCodeGenerationError,
    TooManyRequestError,
    URLNotFoundError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("url_visits")

app = FastAPI(
    title="URL Shortener",
    description="A simple API for shortening URLs and redirecting users.",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


app.include_router(router)


@app.exception_handler(URLNotFoundError)
async def url_not_found_handler(
    request: Request,
    exc: URLNotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={"detail": "Short URL not found"},
    )


@app.exception_handler(ShortCodeGenerationError)
async def handle_short_code_generation_error(
    request: Request,
    exc: ShortCodeGenerationError,
):
    logger.exception(
        "Short code generation failed: %s",
        exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unable to create a shortened URL"
        },
    )


@app.exception_handler(TooManyRequestError)
async def handle_too_many_requests_error(
    request: Request,
    exc: TooManyRequestError,
):
    logger.exception(
        "The number of requests per second exceeded the capacity: %s",
        exc,
    )

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Short-code capacity per second exceeded"
        },
    )


@app.middleware("http")
async def log_short_url_visits(request: Request, call_next):
    response = await call_next(request)

    route = request.scope.get("route")

    if (
        request.method == "GET"
        and getattr(route, "path", None) == "/{short_code}"
        and response.status_code == 307
    ):
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        logger.info(
            "Short URL opened | IP=%s | path=%s",
            client_ip,
            request.url.path,
        )

    return response
