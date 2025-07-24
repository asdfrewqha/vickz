import json
import logging
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        content_type = request.headers.get("content-type", "")
        try:
            if "application/json" in content_type or "text" in content_type:
                body_str = body.decode("utf-8")
            else:
                body_str = f"<binary {len(body)} bytes>"
        except UnicodeDecodeError:
            body_str = f"<undecodable {len(body)} bytes>"

        start = time()
        response: Response = await call_next(request)
        duration = round((time() - start) * 1000, 2)

        log_data = {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "request_body": body_str,
            "status_code": response.status_code,
            "duration_ms": duration,
        }

        if response.headers.get("content-type", "").startswith("application/json"):
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            async def new_body_iterator():
                yield response_body

            response.body_iterator = new_body_iterator()
            try:
                log_data["response_body"] = json.loads(response_body.decode())
            except Exception:
                try:
                    log_data["response_body"] = response_body.decode()
                except:  # noqa
                    log_data["response_body"] = f"<undecodable {len(response_body)} bytes>"

        logger.info(json.dumps(log_data, ensure_ascii=False))
        return response
