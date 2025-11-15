
import secrets
import string
from urllib.parse import urlparse

ALPHABET = string.ascii_letters + string.digits

def generate_slug(length: int = 7) -> str:
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))

def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False
