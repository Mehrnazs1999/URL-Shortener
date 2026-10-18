import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.api import routers
from app.services.exceptions import URLNotFoundError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("url_visits")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener",
    description="A simple API for shortening URLs and redirecting users.",
    version="1.0.0",
)

app.include_router(routers.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


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
