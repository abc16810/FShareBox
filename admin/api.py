from dataclasses import dataclass
from typing import List

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from apps.models import Code_Detail, Codes, Codes_Pydantic, Settings
from common.utils import admin_required, get_app_settings

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse, summary="后台管理首页")
async def index(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@dataclass
class AdminFormParam:
    """admin post parameters."""
    page: int = Form(default=1, description="当前页数")
    size: int = Form(default=10, description="每页显示条数")

    def __post_init__(self):
        pass


@router.post(
    "/",
    summary="后台管理接口",
    dependencies=[Depends(admin_required)],
    response_model=Code_Detail
)
async def get_admin(params=Depends(AdminFormParam)):
    params = params
    total = await Codes.all().count()
    data = await Codes_Pydantic.from_queryset(Codes.all().offset((params.page - 1) * params.size).limit(params.size))
    return {
        'detail': '查询成功',
        'data': data,
        'paginate': {
            'page': params.page,
            'size': params.size,
            'total': total
        }}




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
