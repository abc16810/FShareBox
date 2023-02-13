from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from common.utils import app_settings

from .api import router

admin_set = app_settings.fastapi_kwargs
admin_set['title'] = admin_set.get('title') + " 后台管理"

admin_api = FastAPI(**admin_set)


admin_api.include_router(router, tags=["admin"])


