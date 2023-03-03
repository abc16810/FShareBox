import datetime
import uuid
from dataclasses import dataclass
from typing import List

from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form,
                     HTTPException, Request, UploadFile)
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from admin.lib import admin_required
from apps.models import Codes
from common.utils import (error_ip_limit, get_codes, get_token, storages,
                          upload_ip_limit)

from .schemas import CodeItem, CodeOk, CodeText, HTTPNotFoundError, StyleName

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post(
    "/",
    summary="提交口令",
    response_model=CodeItem,
    responses={
        404: {"model": HTTPNotFoundError, "description": "The item was not found or Code error"},
        400: {"model": HTTPNotFoundError, "description": "Try too many times"}
    }
)
async def get_code(request: Request, code: str, ret: tuple = Depends(error_ip_limit)):
    query = await Codes.get_or_none(code=code)
    ip, set = ret
    if not query:
        error_count = set.error_count - error_ip_limit.add_ip(ip)
        message = f'{error_count} 次后将被禁止 {set.error_minute} 分钟' if error_count else f'禁止 {set.error_minute} 分钟'
        return JSONResponse(status_code=404, content={"detail": f"取件码错误，{message}"})

    if query.exp_time.replace(tzinfo=None) < datetime.datetime.now() or query.count == 0:
        return JSONResponse(status_code=404, content={"detail": "取件码已失效，请联系寄件人"})

    await Codes.filter(id=query.id).update(count=query.count - 1)

    if query.type != 'text':
        query.text = f'/api/select?code={query.code}&token={await get_token(code, ip)}'
    query.text = query.text.replace("\r\n", "</br>")
    return  JSONResponse(content={
        'type': query.type, 
        'text': query.text, 
        'name': query.name, 
        'code': query.code}
        )
 

@router.get(
    "/select",
    summary="文件下载/文本查看",
    response_model=CodeText,
    responses={
        200: {
            "content": {"media": {}},
            "description": "Return the Text item or an File stream.",
        },
        404: {"model": HTTPNotFoundError, "description": "The item was not found"},
        400: {"model": HTTPNotFoundError, "description": "incorrect or expired, and access will be prohibited if the number of times is too many"},
    },
)
async def get_file(code: str, token: str, ret: tuple = Depends(error_ip_limit)):
    ip, _ = ret
    # 验证token
    if token != await get_token(code, ip):
        error_ip_limit.add_ip(ip)
        return JSONResponse(status_code=403, content={"detail": "口令错误，或已过期，次数过多将被禁止访问"})

    # 查出数据库记录
    info = await Codes.get_or_none(code=code)
    if not info:
        error_ip_limit.add_ip(ip)
        return JSONResponse(status_code=404, content={"detail": "口令不存在，次数过多将被禁止访问"})
    # 如果记录不存在，IP错误次数+1

    # 如果是文本，直接返回
    if info.type == 'text':
        return {'text': info.text}
    # 如果是文件，返回文件
    elif storages.name != 'filesystem':
        # 重定向到文件存储服务器
        return RedirectResponse(await storages.get_url(info))
    else:
        filepath = await storages.get_filepath(info.text)
        return FileResponse(filepath, filename=info.name)


@dataclass
class UploadFormParam:
    text: str = Form(default=None, description="文本内容")
    style: str = Form(default=StyleName.two, description="类型 1为次数,2为天数")
    value: int = Form(default=1, description="次数/天数")
    file: List[UploadFile] = File(default=None, description='多个文件')
    background_tasks: BackgroundTasks = BackgroundTasks

    def __post_init__(self):
        value = self.value
        if value < 1:
            raise HTTPException(status_code=400, detail="上传失败! 最小有效次数为1次")
        if self.file:
            filename_list = [file.filename for file in self.file if file.filename.strip()]
            if len(filename_list) == 0:
                self.file = None
        if not self.file:
            if not self.text.strip():
                self.text = None
        if not self.file and not self.text:
            raise HTTPException(status_code=400, detail="上传失败! 文本/文件不能为空")


@router.post(
    "/share",
    summary="分享",
    response_model=CodeOk,
    dependencies=[Depends(admin_required)],
    responses={
        200: {"description": "Return the JSON item.",
              },
        400: {"model": HTTPNotFoundError, "description": "The file is too large"}
    },
)
async def share(request: Request, params=Depends(UploadFormParam), ret: tuple = Depends(upload_ip_limit)):

    ip, set = ret
    exp_time = datetime.datetime.now() + datetime.timedelta(days=1)  # 24小时
    exp_count = -1
    if params.style in StyleName.two:
        if params.value > set.max_days:
            return JSONResponse(status_code=400, content={"detail": f"最大有效天数为{set.max_days}天"})
        exp_time = datetime.datetime.now() + datetime.timedelta(days=params.value)
    elif params.style in StyleName.one:
        if params.value > set.max_times:
            return JSONResponse(status_code=400, content={"detail": f"最大有效次数为{set.max_times}次"})
        exp_count = params.value
    else:
        pass
    bulks = []
    res = []
    if params.file:
        size_list = await storages.get_size(params.file)
        if 0 in size_list:
            return JSONResponse(status_code=400, content={"detail": "上传的文件中不能包括空文件"})
        
        for index, f in enumerate(params.file):
            key = uuid.uuid4().hex
            path_text_list = await storages.get_text(params.file, key)
            code = await get_codes(Codes)
            size = size_list[index]
            text = path_text_list[index]
            t = f.content_type
            name = f.filename
            code_object = await Codes(code=code, text=text, size=size, type=t, name=name, count=exp_count, exp_time=exp_time, key=key)
            bulks.append(code_object)
            res.append({'code': code, 'name': name})
            params.background_tasks.add_task(
                storages.save_file, f, text)
            
    else:
        text_size = len(params.text)
        code = await get_codes(Codes)
        key = uuid.uuid4().hex
        if text_size > 2048:
            return JSONResponse(status_code=400, content={"detail": "上传的文本过大 不能大于2048 byte"})
        size, text, t, name = text_size, params.text, 'text', '文本分享'
        code_object = await Codes(code=code, text=text, size=size, type=t, name=name, count=exp_count, exp_time=exp_time, key=key)
        bulks.append(code_object)
        res.append({'code': code, 'name': name})
    await Codes.bulk_create(bulks)
    upload_ip_limit.add_ip(ip)
    return JSONResponse(status_code=200, content={"data": res})
 