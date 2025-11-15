
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import Optional
import datetime

from database import Base, engine, SessionLocal
from models import URLMap
from cache import LRUCache
from rate_limit import SlidingWindowRateLimiter
from utils import generate_slug, is_valid_url

app = FastAPI(title="Shortie")
Base.metadata.create_all(bind=engine)

cache = LRUCache(capacity=10000)
limiter = SlidingWindowRateLimiter()

class ShortenRequest(BaseModel):
    url: str

class ShortenResponse(BaseModel):
    slug: str
    short_url: str
    long_url: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- Critical function used by endpoints ----
def create_short_url(db: Session, long_url: str) -> str:
    """Create a short, unique slug for long_url with collision retries."""
    # Deduplicate existing
    existing = db.execute(select(URLMap).where(URLMap.long_url == long_url)).scalar_one_or_none()
    if existing:
        return existing.slug

    # Generate slug and ensure uniqueness with up to N retries
    for _ in range(5):
        slug = generate_slug()
        if db.execute(select(URLMap).where(URLMap.slug == slug)).scalar_one_or_none() is None:
            db.add(URLMap(slug=slug, long_url=long_url, click_count=0))
            db.commit()
            return slug
    raise HTTPException(status_code=500, detail="Failed to allocate unique slug")

def resolve_and_track(db: Session, slug: str) -> Optional[str]:
    """Cache-first lookup; on hit return long URL.
       On miss, read DB, update analytics, cache value, return long URL."""
    cached = cache.get(slug)
    if cached is not None:
        # Best-effort async-like analytics update could happen here in prod.
        db.execute(update(URLMap).where(URLMap.slug == slug).values(
            click_count=URLMap.click_count + 1, last_accessed=datetime.datetime.utcnow()
        ))
        db.commit()
        return cached

    row = db.execute(select(URLMap).where(URLMap.slug == slug)).scalar_one_or_none()
    if row is None:
        return None

    cache.set(slug, row.long_url)
    db.execute(update(URLMap).where(URLMap.slug == slug).values(
        click_count=row.click_count + 1, last_accessed=datetime.datetime.utcnow()
    ))
    db.commit()
    return row.long_url

@app.post("/shorten", response_model=ShortenResponse)
def shorten(req: ShortenRequest, request: Request):
    client_ip = request.client.host or "unknown"
    if not limiter.allow(f"shorten:{client_ip}", limit=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    if not is_valid_url(req.url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    with SessionLocal() as db:
        slug = create_short_url(db, req.url)
        short_url = f"{request.base_url}{slug}"
        return ShortenResponse(slug=slug, short_url=short_url, long_url=req.url)

@app.get("/{slug}")
def resolve(slug: str):
    with SessionLocal() as db:
        long_url = resolve_and_track(db, slug)
        if long_url is None:
            raise HTTPException(status_code=404, detail="Not found")
        # Use 307 to preserve method
        return RedirectResponse(url=long_url, status_code=307)

@app.get("/admin/{slug}")
def stats(slug: str):
    with SessionLocal() as db:
        row = db.execute(select(URLMap).where(URLMap.slug == slug)).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Not found")
        return JSONResponse({
            "slug": slug,
            "long_url": row.long_url,
            "click_count": row.click_count,
            "created_at": str(row.created_at),
            "last_accessed": str(row.last_accessed) if row.last_accessed else None
        })
