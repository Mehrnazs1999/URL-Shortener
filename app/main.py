import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.services.exceptions import URLNotFoundError

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


# Register fixed paths before the catch-all /{short_code} redirect route.
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
