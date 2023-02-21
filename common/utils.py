import hashlib
import random
import string
import time
from functools import lru_cache

from fastapi import Request

from apps.models import Codes
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



