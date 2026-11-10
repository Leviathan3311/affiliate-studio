"""In-process sliding-window limits for the public auth endpoints (one API process)."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    # cf-connecting-ip through the tunnel; x-client-ip through the Cloudflare proxy in front of Modal
    h = request.headers
    return (
        h.get("cf-connecting-ip")
        or h.get("x-client-ip")
        or (request.client.host if request.client else "")
    )


def limit(key: str, max_hits: int, window_s: int) -> None:
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > window_s:
        q.popleft()
    if len(q) >= max_hits:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Thử quá nhiều lần, vui lòng đợi ít phút rồi thử lại"
        )
    q.append(now)


def reset() -> None:
    _hits.clear()
