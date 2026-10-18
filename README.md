# URL Shortener

A FastAPI service that creates short URLs, redirects visitors, counts visits,
and logs successful redirect requests with the client IP and timestamp.

## Requirements implemented

- `POST /shorten` accepts an `original_url` and returns a short code.
- `GET /{short_code}` responds with a temporary redirect and increments the
  visit count.
- `GET /stats/{short_code}` returns the visit count.
- URLs are persisted with an original URL, unique short code, creation time,
  and click count.
- Redirect logging is centralized in middleware.

Alembic migrations and scalability work are intentionally not included yet.

## Run locally

Create a PostgreSQL database and set `DATABASE_URL` in `.env` to a reachable
instance. For the checked-in default value, that means:

```bash
createdb url_shortener
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

The API is then available at `http://localhost:8000`, with interactive
documentation at `http://localhost:8000/docs`.

The application creates the `urls` table at startup until Alembic migrations
are added. If PostgreSQL is not running or `url_shortener` has not been
created, startup will fail with a database connection error.

## Test

```bash
python3 -m pytest -q
```

Tests use an isolated in-memory SQLite database, so they do not need a local
PostgreSQL server.
