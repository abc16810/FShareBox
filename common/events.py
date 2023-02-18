
# coding: utf-8
import asyncio
import datetime
from typing import Callable

from fastapi import FastAPI
from tortoise.expressions import Q

from apps import models
from settings import AppSettings

from .utils import error_ip_limit, storages, upload_ip_limit


async def init_db(app: FastAPI, settings: AppSettings) -> None:
    # 初始化数据
    if not await models.Settings.exists():
        await models.Settings.create()
    app.state.settings = await models.Set_Pydantic.from_queryset_single(models.Settings.first())


# type: ignore
def create_start_app_handler(app: FastAPI, settings: AppSettings) -> Callable:
    async def start_app() -> None:
        await init_db(app, settings)
        asyncio.create_task(
            delete_expire_files(settings))

    return start_app


# 后台定时任务
async def delete_expire_files(set: AppSettings):
    while True:
        await error_ip_limit.remove_expired_ip()
        await upload_ip_limit.remove_expired_ip()
        query = await models.Codes.filter(
            Q(exp_time__lt=datetime.datetime.now()) | Q(count=0)
        )
        files = []
        exps_ids = []
        for q in query:
            if q.type != "text":
                files.append(q.text)
            exps_ids.append(q.id)
        await storages.delete_files(files)
        await models.Codes.filter(id__in=exps_ids).delete()
        await asyncio.sleep(set.delete_expire_file_interval * 60)
