import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List

import aiofiles
from fastapi import UploadFile

from settings import AppSettings


class AliyunFileStorage:
    name = "aliyunsystem"

    def __init__(self, set: AppSettings):
        pass


class FileSystemStorage:
    name = "filesystem"

    def __init__(self, set: AppSettings):
        self.upload_dir = Path(set.data_root)
        self.static_url = set.static_url

    async def get_filepath(self, text: str):
        return self.upload_dir / text.lstrip(self.static_url + '/')

    @staticmethod
    async def get_size(files: List[UploadFile]) -> List[int]:
        res = []
        for file in files:
            f = file.file
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0, os.SEEK_SET)
            res.append(size)
        return res

    async def get_text(self, files: List[UploadFile], key: str) -> List[str]:
        now = datetime.now()
        path = self.upload_dir / f"upload/{now.year}/{now.month}/{now.day}/"
        res = []
        if not path.exists():
            path.mkdir(parents=True)

        for file in files:
            ext = file.filename.split('.')[-1]
            text = f"{self.static_url}/{(path / f'{key}.{ext}').relative_to(self.upload_dir)}"
            res.append(text)
        return res

    async def save_file(self, file: UploadFile, text: str) -> None:
        filepath = await self.get_filepath(text)
        async with aiofiles.open(filepath, 'wb') as f:
            chunk_size = 256 * 1024
            chunk = await file.read(chunk_size)
            while chunk:
                await f.write(chunk)
                chunk = await file.read(chunk_size)

    def judge_delete_folder(self, filepath):
        current = filepath.parent
        while current != self.upload_dir:
            if not list(current.iterdir()):
                os.rmdir(current)
                current = current.parent
            else:
                break

    async def delete_file(self, text: str):
        filepath = await self.get_filepath(text)
        if filepath.exists():
            # ?????????????????????????????????????????? python3.9+
            # await asyncio.to_thread(os.remove, filepath)
            # await asyncio.to_thread(self.judge_delete_folder, filepath)
            await asyncio.get_running_loop().run_in_executor(None, os.remove, filepath)
            await asyncio.get_running_loop().run_in_executor(None, self.judge_delete_folder, filepath)

    async def delete_files(self, files: List):
        tasks = [self.delete_file(text) for text in files]
        await asyncio.gather(*tasks)  # ????????????task
