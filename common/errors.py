from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.logger import logger
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR


async def server_500_error_exception(request: Request, exc: HTTPException) -> JSONResponse:
    logger.info(f"An HTTP error!: {repr(exc)}")
    return await http_exception_handler(request, exc)


async def validation_error_handler(_: Request, exc):
    logger.error(f"字段值验证错误!: {exc}")
    return JSONResponse(
        {"detail": "System Error"},
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )
