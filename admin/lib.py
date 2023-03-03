import time
from typing import Union

from fastapi import Depends, HTTPException, Request
from fastapi.logger import logger
from fastapi.security.api_key import APIKeyCookie
from jose import JWTError, jwt
from pydantic import BaseModel

from apps.models import Set_Pydantic, Settings
from common.utils import app_settings
from settings import AppSettings

# openssl rand -hex 32
SECRET_KEY = "343ca65e419bddd55794cba36fe39cc18fb7c7fb9f44ec825e7dd644f4be46ab"
ALGORITHM = "HS256"

api_key_cookie = APIKeyCookie(name='token', auto_error=False)


class Passwd(BaseModel):
    password: str


async def decode_token(token: str, set: AppSettings) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        passwd: str = payload.get("token")
        if not passwd.strip() or passwd != set.api_manager_password:
            raise HTTPException(status_code=401, detail="密码错误，请重新登录")
        return True
    except (JWTError, Exception) as err:
        logger.warn("%s" % str(err))
        return False


def create_access_token(data: dict, exp_minutes: Union[int, None] = None):
    to_encode = data.copy()
    if exp_minutes:
        expire = time.time() + exp_minutes * 60
    else:
        expire = time.time() + 15 * 60
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_passwd(set, password: str) -> bool:
    if set.api_manager_password != password:
        return False
    return True

# 自定义分页 弃用
async def paginator_num(total_page: int, current_page: int) -> list:
    DOT = '.'
    ON_EACH_SIDE = 2
    ON_ENDS = 2
    if total_page <= 10:
        page_range = range(1, total_page + 1)
    else:
        page_range = []
        if current_page > (ON_EACH_SIDE + ON_ENDS + 1):
            page_range.extend(range(1, ON_ENDS + 1))
            page_range.append(DOT)
            page_range.extend(
                range(current_page - ON_EACH_SIDE, current_page + 1))
        else:
            page_range.extend(range(1, current_page + 1))
        if current_page < (total_page - ON_EACH_SIDE - ON_ENDS):
            page_range.extend(
                range(current_page + 1, current_page + ON_EACH_SIDE + 1))
            page_range.extend(DOT)
            page_range.extend(range(total_page - ON_ENDS + 1, total_page + 1))
        else:
            page_range.extend(range(current_page + 1, total_page + 1))
    return list(page_range)



# admin
async def admin_checked(token: str = Depends(api_key_cookie)):
    if not token or not await decode_token(token, app_settings):
        raise HTTPException(status_code=403, detail="认证失败，请重新登录")


async def admin_required(token: str = Depends(api_key_cookie), request: Request = None):
    set = await Set_Pydantic.from_queryset_single(Settings.first())
    if not await decode_token(token, app_settings) and not set.enable_upload:
        raise HTTPException(status_code=403, detail='本站上传功能已关闭，仅管理员可用')

    request_file_size = request.headers.get('content-length', '0')
    if int(request_file_size) > set.upload_file_size - 500:
        raise HTTPException(
                status_code=400, detail='超过最大文件大小限度')
    