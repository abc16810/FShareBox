

import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.logger import logger
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_403_FORBIDDEN
from starlette.types import ASGIApp

from common.utils import app_settings

from .api import router

admin_set = app_settings.fastapi_kwargs
admin_set['title'] = admin_set.get('title') + " 后台管理"




async def forbidden_error_exception(request: Request, exc: HTTPException) -> RedirectResponse:
    logger.info("error: %s" % exc.detail)
    return RedirectResponse(url='/', status_code=302)


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

# 403
admin_api.add_exception_handler(HTTP_403_FORBIDDEN, forbidden_error_exception)

# 422
@admin_api.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warn(f"The client sent invalid data!: {exc}")
    return JSONResponse(status_code=400, content={"detail": "字段值错误，请检查字段值是否合法"})


admin_api.include_router(router, tags=["admin"])
