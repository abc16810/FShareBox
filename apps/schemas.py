from enum import Enum
from typing import List, Union

from pydantic import BaseModel


class CodeBase(BaseModel):
    code: str
    name: str


class CodeOk(BaseModel):
    data: List[CodeBase]
    

class HTTPNotFoundError(BaseModel):
    detail: str


class CodeText(BaseModel):
    text: str


class CodeItem(CodeText):
    type: str
    name: str
    code: str


class StyleName(str, Enum):
    one = "1"  # 文本
    two = "2"  # 文件