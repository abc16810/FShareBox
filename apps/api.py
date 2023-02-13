import datetime
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Union

from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form,
                     HTTPException, Request, UploadFile)
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from apps.models import Codes, Detail, OkItem, Set_Pydantic, Settings
from common.utils import (admin_required, app_settings, error_ip_limit,
                          get_codes, get_token, storages, upload_ip_limit)

router = APIRouter()


@router.get("/info")
async def info(request: Request):
    return {
        "name": "11",
        "author": "22"
    }


@router.post(
    "/",
    summary="获取链接",
    response_model=OkItem,
    responses={
        200: {
            "description": "Return the JSON item.",
        },
        404: {"model": Detail, "description": "The item was not found or Code error"},
        400: {"model": Detail, "description": "Try too many times"}
    }
)
async def get_code(request: Request, code: str, ret: tuple = Depends(error_ip_limit)):
    """获取下载链接"""
    query = await Codes.get_or_none(code=code)
    ip, set = ret
    if not query:
        error_count = set.error_count - error_ip_limit.add_ip(ip)
        raise HTTPException(
            status_code=404, detail=f"取件码错误，{error_count}次后将被禁止{set.error_minute}分钟")

    if query.exp_time.replace(tzinfo=None) < datetime.datetime.now() or query.count == 0:
        raise HTTPException(status_code=404, detail="取件码已失效，请联系寄件人")

    await Codes.filter(id=query.id).update(count=query.count - 1)

    if query.type != 'text':
        query.text = f'/api/select?code={query.code}&token={await get_token(code, ip)}'
    return {
        'detail': f'取件成功，请立即下载，避免失效！',
        'data': {'type': query.type, 'text': query.text, 'name': query.name, 'code': query.code}
    }


@router.get(
    "/select",
    summary="文件下载链接",
    response_model=OkItem,
    responses={
        200: {
            "content": {"media": {}},
            "description": "Return the JSON item or an File stream.",
        },
        404: {"model": Detail, "description": "The item was not found"},
        403: {"model": Detail, "description": "incorrect or expired, and access will be prohibited if the number of times is too many"},
    },
)
async def get_file(code: str, token: str, ret: tuple = Depends(error_ip_limit)):
    ip, set = ret
    # 验证token
    if token != await get_token(code, ip):
        error_ip_limit.add_ip(ip)
        raise HTTPException(status_code=403, detail="口令错误，或已过期，次数过多将被禁止访问")

    # 查出数据库记录
    info = await Codes.get_or_none(code=code)
    if not info:
        error_ip_limit.add_ip(ip)
        raise HTTPException(status_code=404, detail="口令不存在，次数过多将被禁止访问")
    # 如果记录不存在，IP错误次数+1

    # 如果是文本，直接返回
    if info.type == 'text':
        return {'detail': '查询成功', 'data': info.text}
    # 如果是文件，返回文件
    elif storages.name != 'filesystem':
        # 重定向到文件存储服务器
        return RedirectResponse(await storages.get_url(info))
    else:
        filepath = await storages.get_filepath(info.text)
        return FileResponse(filepath, filename=info.name)


class StyleName(str, Enum):
    one = "1"
    two = "2"


@dataclass
class UploadFormParam:
    """file/text upload parameters."""
    text: str = Form(default=None, description="文本内容")
    style: str = Form(default=StyleName.two, description="类型 1为次数,2为天数")
    value: int = Form(default=1)
    file: UploadFile = File(default=None, description='文件')
    background_tasks: BackgroundTasks = BackgroundTasks

    def __post_init__(self):
        value = self.value
        if value < 1:
            raise HTTPException(status_code=400, detail="最小有效次数为1次")
        if not self.file and not self.text:
            raise HTTPException(status_code=400, detail="文本不能为空")


@router.post(
    "/share",
    summary="分享",
    response_model=OkItem,
    dependencies=[Depends(admin_required)],
    responses={
        200: {"description": "Return the JSON item.",
              },
        400: {"model": Detail, "description": "The file is too large"}
    },
)
async def share(request: Request, params=Depends(UploadFormParam), ret: tuple = Depends(upload_ip_limit)):
    """文件分享接口"""
    code = await get_codes(Codes)
    ip, set = ret
    exp_time = datetime.datetime.now() + datetime.timedelta(days=1)  # 24小时
    exp_count = -1
    if params.style in StyleName.two:
        if params.value > set.max_days:
            raise HTTPException(
                status_code=400, detail=f"最大有效天数为{set.max_days}天")
        exp_time = datetime.datetime.now() + datetime.timedelta(days=params.value)
    elif params.style in StyleName.one:
        exp_count = params.value
    else:
        pass
    key = uuid.uuid4().hex
    if params.file:
        size = await storages.get_size(params.file)
        if size > set.upload_file_size:
            raise HTTPException(status_code=400, detail="文件过大")
        _text, _type, name = await storages.get_text(params.file, key), params.file.content_type, params.file.filename
        params.background_tasks.add_task(
            storages.save_file, params.file, _text)

    else:
        text_size = len(params.text)
        if text_size > 2048:
            raise HTTPException(status_code=400, detail="文本过大")
        size, _text, _type, name = text_size, params.text, 'text', '文本分享'
    await Codes.create(code=code, text=_text, size=size, type=_type, name=name, count=exp_count, exp_time=exp_time, key=key)
    upload_ip_limit.add_ip(ip)
    return {
        'detail': '分享成功，请点击我的文件按钮查看上传列表',
        'data': {'code': code, 'key': key, 'name': name}
    }
