from typing import Union

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import ValidationError

from admin.routes import admin_api
from apps import api, views
from common.errors import server_500_error_exception, validation_error_handler
from common.events import create_start_app_handler
from common.utils import app_settings


def get_application() -> FastAPI:

    settings = app_settings
    application = FastAPI(**settings.fastapi_kwargs)

    # 限速
    # application.state.limiter = limiter
    # application.add_exception_handler(
    #     RateLimitExceeded, _rate_limit_exceeded_handler)

    # 链接数据库
    register_tortoise(application,
                      config={
                          "connections": {
                              "default": {
                                  'engine': 'tortoise.backends.sqlite',
                                  "credentials": {"file_path": "%s" % settings.db_file},
                              }
                          },
                          "apps": {
                              "models": {
                                  "models": ["apps.models"],
                                  "default_connection": "default",
                              }
                          },
                      },
                      generate_schemas=True   # 生成数据库schema
                      )

    application.add_event_handler(
        "startup",
        create_start_app_handler(application, settings)
    )

    # 静态文件夹
    application.mount(
        "/static", StaticFiles(directory="static"), name="static")
    # router
    application.include_router(views.router)
    application.include_router(api.router, prefix=settings.api_prefix)
    # admin router
    application.mount(settings.api_manager_prefix, admin_api)


    # errors
    application.add_exception_handler(
        ValidationError, validation_error_handler)
    application.add_exception_handler(
        HTTP_500_INTERNAL_SERVER_ERROR, server_500_error_exception)

    return application


app = get_application()

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="10.4.55.235",
                port=8082, reload=True, log_level="debug")
