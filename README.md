Here’s a clean README you can drop into your GitHub repo. I also saved it as a file you can download.

[Download README_BlinkRoute.md](sandbox:/mnt/data/README_Shortie.md)

---

# BlinkRoute — fast redirects that happen in a blink.

BlinkRoute is a small web service that creates short links, redirects them fast using a cache, and tracks basic click stats.
It is written with FastAPI and SQLAlchemy. The repo is simple to read, easy to run locally, and has a clear path to production.

---

## Features

* Create short URLs with automatic 7-character slug generation
* Fast redirects with a cache-first lookup
* Basic click analytics: total clicks and last accessed timestamp
* Per-IP rate limiting on the `POST /shorten` endpoint (sliding window)
* SQLite for local development; easy swap to Postgres for production

---

## Tech Stack

* **API:** FastAPI
* **ORM:** SQLAlchemy
* **Database:** SQLite (local) → Postgres (recommended for prod)
* **Caching:** In-memory LRU (local) → Redis (recommended for prod)
* **Server:** Uvicorn (ASGI)

---

## Quick Start (Local)

Requirements: Python 3.10+

```bash
# Clone your repo, then from the project root:
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Now the API is available at `http://127.0.0.1:8000`.

---

## API Reference

### 1) Create a short URL

`POST /shorten`

**Request body**

```json
{ "url": "https://example.com/some/long/path" }
```

**Response**

```json
{
  "slug": "abc12Xy",
  "short_url": "http://127.0.0.1:8000/abc12Xy",
  "long_url": "https://example.com/some/long/path"
}
```

**Example (curl)**

```bash
curl -X POST http://127.0.0.1:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

---

### 2) Redirect by slug

`GET /{slug}`

Redirects with HTTP 307 to the original URL.

**Example**
Open `http://127.0.0.1:8000/abc12Xy` in your browser.

---

### 3) View stats for a slug

`GET /admin/{slug}`

**Response**

```json
{
  "slug": "abc12Xy",
  "long_url": "https://example.com",
  "click_count": 5,
  "created_at": "2025-11-15 10:00:00",
  "last_accessed": "2025-11-15 10:05:10"
}
```

---

## How It Works

### Architecture (Mermaid)

```mermaid
flowchart LR
  U[User/Browser] --> F[FastAPI]
  F -->|POST /shorten| S[(DB)]
  F -->|GET /{slug}| C{Cache}
  C -->|miss| S
  S -->|long_url| C
  F -->|redirect| U
  F -->|GET /admin/{slug}| S
```

* **Write path (`POST /shorten`):** validate URL → check if it already exists → generate a unique slug → save to DB.
* **Read path (`GET /{slug}`):** cache-first lookup; on miss, load from DB, update analytics, and cache the value.
* **Admin stats:** fetch current stats from DB.

### Data Model

Table: `url_map`

| Column          | Type     | Notes                          |
| --------------- | -------- | ------------------------------ |
| `id`            | Integer  | Primary key                    |
| `slug`          | String   | Unique index, 7 chars (base62) |
| `long_url`      | String   | Original URL                   |
| `click_count`   | Integer  | Total redirects                |
| `created_at`    | DateTime | Row creation time              |
| `last_accessed` | DateTime | Last successful redirect time  |

---

## Configuration

Local development uses SQLite out of the box (see `database.py`).
To use Postgres, update `SQLALCHEMY_DATABASE_URL` in `database.py`, for example:

```python
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:5432/shortie"
```

Caching and rate limiting are in-memory for local use. In production, use Redis for both.

---

## Rate Limiting

* Endpoint: `POST /shorten`
* Policy: sliding window per IP (default in-memory for demo)
* In production, store counters in Redis so the limit applies across multiple app instances.

---

## Caching

* Key: `slug` → `long_url`
* Local: in-memory LRU cache
* Production: Redis (set TTLs and consider cache warming for hot slugs)

---

## Testing (suggested)

* New URL returns a new slug
* Same URL returns the same slug (idempotent behavior)
* Forced slug collision retries and eventually succeeds
* Invalid URL returns HTTP 400
* Rate limit triggers 429 after threshold within the time window

---

## Deployment Notes

* Run behind a reverse proxy (Nginx/Envoy) and use a process manager (e.g., Gunicorn with Uvicorn workers).
* Set up Postgres and Redis services.
* Enable HTTPS and HSTS at the proxy/CDN layer.
* Add dashboards for latency, error rate, and redirect throughput.

---

## Security Notes

* Validate input URLs (scheme must be `http` or `https`).
* Consider a domain allow/deny list for production.
* Sanitize logs; avoid logging full query strings if they contain secrets.

---

## Roadmap

* Custom slugs (with validation)
* Expiring links
* Per-slug analytics (unique visitors, referrer, user agent)
* OpenAPI examples and Postman collection
* Dockerfile and docker-compose for local dev

---

## Project Files

* `app.py` — FastAPI app and endpoints
* `models.py` — SQLAlchemy model(s)
* `database.py` — DB engine/session config
* `cache.py` — simple LRU cache
* `rate_limit.py` — in-memory sliding window limiter
* `utils.py` — helpers (slug generation, URL validation)
* `requirements.txt` — Python dependencies

---

## License

MIT
