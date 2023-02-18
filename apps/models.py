# coding: utf-8
from typing import Any, Dict, List, Union

from pydantic import BaseModel
from tortoise import Model, fields
from tortoise.contrib.pydantic import pydantic_model_creator


class OkItem(BaseModel):
    detail: str
    data: Union[str, Dict[str, Any]]


class Detail(BaseModel):
    detail: str


class Settings(Model):
    """系统设置"""
    id = fields.IntField(pk=True)
    enable_upload = fields.BooleanField(description="是否开启上传", default=True)
    max_days = fields.SmallIntField(description="最长保存天数", default=7)
    max_times = fields.SmallIntField(description="最大下载次数", default=10)
    error_count = fields.SmallIntField(description="失败次数", default=5)
    error_minute = fields.SmallIntField(description="错误限制分钟数", default=10)
    upload_count = fields.SmallIntField(description="上传次数", default=60)
    upload_minute = fields.SmallIntField(description="上传限制分钟数", default=1)
    upload_file_size = fields.IntField(
        description="上传文件大小 Byte", default=10485760)  # 10M 10*1024*1024

    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "settings"


Set_Pydantic = pydantic_model_creator(Settings, name="Settings")


class Codes(Model):
    """Code"""
    id = fields.IntField(pk=True, index=True)
    code = fields.CharField(unique=True, max_length=10, index=True)
    key = fields.CharField(max_length=32, unique=True)
    name = fields.CharField(max_length=500, description="分享类型名称")
    size = fields.IntField()
    type = fields.CharField(max_length=200, description="类型")
    text = fields.TextField()
    used = fields.BooleanField(default=False)
    count = fields.IntField(default=-1, description="有效次数")

    use_time = fields.DatetimeField(auto_now_add=True)
    exp_time = fields.DatetimeField(null=True, description="过期时间")

    class Meta:
        table = "codes"

    def get_texts(self) -> str:
        if self.type == "text":
            if len(self.text) > 20:
                return self.text[:20] + "..."
            return self.text
        else:
            return f'/api/select?code={self.code}'

    def get_type(self) -> str:
        if self.type == "text":
            return '文本'
        else:
            return '文件'

    def get_short_text(self) -> str:
        if self.type == "text":
            return self.text[:1024]
        return '11'

    class PydanticMeta:
        computed = ["get_texts", "get_type", "get_short_text"]


Codes_Pydantic = pydantic_model_creator(
    Codes, name="Codes", include=("id", "code", "name", "exp_time", "count", "size"), computed=['get_texts', "get_type", "get_short_text"])


class Code_Detail(BaseModel):
    detail: str
    data: List
    paginate: Dict['str', int]
