import hashlib
import random
import string
import time
from functools import lru_cache

from fastapi import Header, HTTPException, Request

from apps.models import Codes, Set_Pydantic
from apps.models import Settings as set_db
from settings import AppSettings

from .depends import IPRateLimit
from .storage import AliyunFileStorage, FileSystemStorage


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


def get_ipaddr(request: Request) -> str:
    return request.get("X-Real-IP", request.headers.get("X_FORWARDED_FOR", request.client.host or '127.0.0.1'))


async def get_codes(code: Codes) -> str:
    str_code = random.sample(string.ascii_letters + string.digits, 5)
    code = ''.join(str_code)
    while (await Codes.filter(code=code)):
        str_code = random.sample(string.ascii_letters + string.digits, 5)
        code = ''.join(str_code)
    return code


async def get_token(ip, code):
    return hashlib.sha256(f"{ip}{code}{int(time.time() / 1000)}000".encode()).hexdigest()

# 限速
# limiter = Limiter(key_func=get_ipaddr)

app_settings = get_app_settings()

upload_ip_limit = IPRateLimit(False)
error_ip_limit = IPRateLimit(True)


STORAGE_ENGINE = {
    "filesystem": FileSystemStorage(app_settings),
    "aliyunsystem": AliyunFileStorage(app_settings)
}
storages = STORAGE_ENGINE[app_settings.storage_engine]


# admin
async def admin_required(token: str = Header(default=None), request: Request = None):

    if not await set_db.exists():
        raise HTTPException(detail="System Error", status_code=500)
    set = await Set_Pydantic.from_queryset_single(set_db.first())
    if 'share' in request.url.path:
        if token != app_settings.api_manager_password and not set.enable_upload:
            raise HTTPException(status_code=403, detail='本站上传功能已关闭，仅管理员可用')
    else:
        if not app_settings.api_manager_password:
            raise HTTPException(
                status_code=404, detail='您未设置管理员密码，无法使用此功能，请更新配置文件后，重启系统')
        if not token or token != app_settings.api_manager_password:
            raise HTTPException(status_code=401, detail="密码错误，请重新登录")
