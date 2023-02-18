

import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from common.utils import app_settings
from starlette.types import ASGIApp

from .api import router

admin_set = app_settings.fastapi_kwargs
admin_set['title'] = admin_set.get('title') + " 后台管理"

admin_api = FastAPI(**admin_set)


class CheckPassWordMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: ASGIApp, set: app_settings) -> None:
        """Init Middleware."""
        super().__init__(app)
        self.set = set
        self.key = 'token'

    async def dispatch(self, request: Request, call_next):
        """Add cookie check."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


admin_api.add_middleware(CheckPassWordMiddleware, **{"set": app_settings})
admin_api.include_router(router, tags=["admin"])
