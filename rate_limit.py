
import time
from collections import defaultdict, deque

class SlidingWindowRateLimiter:
    """In-memory per-process sliding window limiter."""
    def __init__(self):
        self.windows = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        dq = self.windows[key]
        # Drop events outside the window
        while dq and dq[0] <= now - window_seconds:
            dq.popleft()
        if len(dq) < limit:
            dq.append(now)
            return True
        return False
