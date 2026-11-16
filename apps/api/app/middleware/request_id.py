from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a correlation X-Request-ID header to every HTTP request and response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming.strip() if incoming and len(incoming.strip()) <= 64 else str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
