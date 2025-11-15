
# BlinkRoute — URL Shortener (FastAPI)

BlinkRoute creates short links, redirects them quickly using a cache, and tracks basic click stats.

## Architecture

Paste this Mermaid block exactly as-is in GitHub:

```mermaid
flowchart LR
    U[User/Browser] --> F[FastAPI]
    F -->|POST /shorten| S[(DB)]
    F -->|GET /{slug}| C[Cache]
    C -->|miss| S
    S -->|long_url| C
    F -->|redirect| U
    F -->|GET /admin/{slug}| S
```

If GitHub still won't render, use the text fallback below.

### Text fallback
```
User -> FastAPI -> (POST /shorten) -> DB
User -> FastAPI -> (GET /{slug}) -> Cache -> (miss) -> DB -> Cache
FastAPI -> redirect -> User
FastAPI -> (GET /admin/{slug}) -> DB
```
