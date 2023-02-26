import math
from dataclasses import dataclass
from typing import List
from fastapi import (APIRouter, Body, Depends, Form, HTTPException,
                     Request, Response, BackgroundTasks)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from apps.models import Codes, Codes_Pydantic, Detail, Settings
from common.utils import app_settings, get_app_settings, storages

from .lib import (admin_checked, api_key_cookie, authenticate_passwd,
                  create_access_token, decode_token)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@dataclass
class TokenParam:
    token: str = Depends(api_key_cookie)

    def __post_init__(self):
        if not app_settings.api_manager_password:
            raise HTTPException(
                status_code=403, detail='您未设置管理员密码，无法使用此功能，请更新配置文件后，重启系统')
        token = self.token
        if token:
            self.token = token.strip()


@router.get(
    "/login",
    response_class=HTMLResponse,
    summary="后台登陆"
)
async def login_index(request: Request, set=Depends(get_app_settings), params=Depends(TokenParam)):
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


@dataclass
class LoginFormParam:
    """Login Form"""
    password: str = Form(description="登陆密码")

    def __post_init__(self):
        value = self.password.strip()
        if not value:
            raise HTTPException(status_code=400, detail="密码不能为空")
        self.password = str(value)


@router.post(
    "/login",
    response_class=RedirectResponse,
    responses={
        '400': {"model": Detail, "description": "Authentication failed"}
    }
)
async def login(
    request: Request,
    response: Response,
    set=Depends(get_app_settings),
    params=Depends(TokenParam),
    form: LoginFormParam = Depends(LoginFormParam),
):
    token = params.token
    if token and await decode_token(token, set):
        # 如果登录跳转到首页
        return RedirectResponse("%s" % set.api_manager_prefix)
    check = authenticate_passwd(set, form.password)
    if not check:
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )
    data = {"token": form.password}
    access_token_expires = set.api_manager_password_expire_minute

    access_token = create_access_token(
        data=data, exp_minutes=access_token_expires)
    response = RedirectResponse(url='/admin', status_code=303)
    response.set_cookie(key="token", value=access_token)
    return response


# @dataclass
# class AdminFormParam:
#     """admin post parameters."""
#     page: int = Query(default=1, description="当前页数")
#     size: int = Query(default=10, description="每页显示条数")


@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(admin_checked)],
    summary="后台管理首页"
)
async def index(
    request: Request,
):
    return templates.TemplateResponse("admin.html", {"request": request})


@router.get(
    "/list",
    dependencies=[Depends(admin_checked)],
    response_model=List[Codes_Pydantic]
)
async def file_list(
    request: Request,
    set=Depends(get_app_settings)
):
    return await Codes_Pydantic.from_queryset(Codes.all())


@router.delete(
    "/code/{code_id}",
    dependencies=[Depends(admin_checked)],
    response_model=Detail,
    responses={404: {"model": Detail}}
)
async def delete_user(code_id: int, background_tasks: BackgroundTasks):
    deleted_item = await Codes.filter(id=code_id)
    if not deleted_item:
        raise HTTPException(
            status_code=404, detail=f"Code {code_id} not found")
    item = deleted_item[0]
    await item.delete()
    if item.type != "text":
        background_tasks.add_task(
            storages.delete_files, [item.text])
    return Detail(detail=f"Deleted code {code_id}")


@router.get(
    "/config",
    response_class=HTMLResponse,
    dependencies=[Depends(admin_checked)],
    description="获取系统配置"
)
async def config(
    request: Request,
    set=Depends(get_app_settings)
):
    settings = await Settings.first()
    return templates.TemplateResponse(
        "config.html",
        context={
            "request": request,
            'prefix': set.api_manager_prefix,
            'settings': settings
        },
        media_type="text/html")


@dataclass
class PutParams:
    """Put parameters."""

    enable_upload: bool = Body(
        default=True
    )
    max_days: int = Body(
        ge=1, lt=365, default=7
    )
    max_times: int = Body(
        ge=1, lt=10000, default=10
    )
    error_count: int = Body(
        ge=1, lt=100, default=5
    )
    error_minute: int = Body(
        ge=1, lt=100, default=5
    )
    upload_count: int = Body(
        ge=1, lt=100, default=5
    )
    upload_minute: int = Body(
        ge=1, lt=100, default=5
    )
    upload_file_size: int = Body(
        ...,  gt=1, le=10485760
    )


@router.put(
    "/config",
    dependencies=[Depends(admin_checked)],
    description="修改系统配置",
    response_model=Detail,
    responses={
        200: {
            "description": "Return the JSON item.",
        }
    }
)
async def config_put(
    request: Request,
    item=Depends(PutParams)
):
    await Settings.all().update(**item.__dict__)
    return {"detail": "更新成功"}
