from fastapi import Security
from fastapi.security.api_key import APIKeyCookie
from datetime import timedelta
from dataclasses import dataclass
import time
import math
from typing import List, Union
from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi import (APIRouter, Depends, Form, HTTPException, Query, Request,
                     Response)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from apps.models import Detail
from apps.models import Code_Detail, Codes, Codes_Pydantic, Settings
from common.utils import admin_required, get_app_settings
from settings import AppSettings

router = APIRouter()
templates = Jinja2Templates(directory="templates")
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
        print(passwd)
        if not passwd.strip() and passwd != set.api_manager_password:
            raise HTTPException(status_code=401, detail="密码错误，请重新登录")
        return True
    except JWTError:
        return False


@dataclass
class TokenParam:
    token: str = Depends(api_key_cookie)

    def __post_init__(self):
        token = self.token
        if token:
            self.token = token.strip()


@router.get(
    "/login",
    response_class=HTMLResponse,
    summary="后台登陆"
)
async def index(request: Request, set=Depends(get_app_settings), params=Depends(TokenParam)):
    token = params.token
    if token and await decode_token(token, set):
        # 如果登录跳转到首页
        return RedirectResponse("%s" % set.api_manager_prefix)
    return templates.TemplateResponse(
        "login.html",
        context={
            "request": request,
            "des": set.description,
            "title": set.title,
            "keywords": set.keywords
        },
        media_type="text/html"
    )


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = time.time() + expires_delta
    else:
        expire = time.time() + 15 * 60
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_passwd(set, password: str) -> bool:
    if set.api_manager_password != password:
        return False
    return True


@dataclass
class LoginFormParam:
    """Login Form"""
    password: str = Form(description="登陆密码")

    def __post_init__(self):
        value = self.password.strip()
        if not value:
            raise HTTPException(status_code=400, detail="密码不能为空")
        self.password = str(value)


@router.post("/login",
             response_model=Detail,
             responses={
                 '400': {"model": Detail, "description": "Authentication failed"}
             }
             )
async def login(
    request: Request,
    response: Response,
    set=Depends(get_app_settings),
    form: LoginFormParam = Depends(LoginFormParam),
):
    check = authenticate_passwd(set, form.password)
    if not check:
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )
    data = {"token": form.password}
    access_token_expires = 20000

    access_token = create_access_token(
        data=data, expires_delta=access_token_expires)
    response.set_cookie(key="token", value=access_token)
    return {"detail": "/admin"}


@dataclass
class AdminFormParam:
    """admin post parameters."""
    page: int = Query(default=1, description="当前页数")
    size: int = Query(default=10, description="每页显示条数")

    def __post_init__(self):
        pass


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


@router.get(
    "/",
    response_class=HTMLResponse,
    summary="后台管理首页"
)
async def index(request: Request, set=Depends(get_app_settings), params=Depends(TokenParam), info=Depends(AdminFormParam)):
    token = params.token
    if not token or not await decode_token(token, set):
        print('222', token)
        return RedirectResponse('/')
    total = await Codes.all().count()
    print(info.page, info.size)
    data = await Codes_Pydantic.from_queryset(Codes.all().offset((info.page - 1) * info.size).limit(info.size))
    page_range = await paginator_num(math.ceil(total/info.size), info.page)
    return templates.TemplateResponse(
        "admin.html",
        context={
            "request": request,
            "data": data,
            'page': info.page,
            'size': info.size,
            'total': total,
            'page_range': page_range
        },
        media_type="text/html")


@router.get(
    '/config',
    description='获取系统配置',
    dependencies=[Depends(admin_required)]
)
async def config():
    # 查询数据库
    data = {}

    return {'detail': '获取成功', 'data': {"id": 1, "key": "22"}, 'menus': [
        {'key': 'INSTALL', 'name': '版本信息'},
        {'key': 'WEBSITE', 'name': '网站设置'},
        {'key': 'SHARE', 'name': '分享设置'},
        {'key': 'BANNERS', 'name': 'Banner'},
    ]}
