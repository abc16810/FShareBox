# coding: utf-8
from typing import Any, Dict, List, Union

from pydantic import BaseModel
from tortoise import Model, fields
from tortoise.contrib.pydantic import pydantic_model_creator


class TimestampMixin():
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

class MyAbstractBaseModel(Model):
    id = fields.IntField(pk=True)
    enable_upload = fields.BooleanField(description="是否开启上传", default=True)
    class Meta:
        abstract = True
        
class Settings(TimestampMixin, MyAbstractBaseModel):
    id = fields.UUIDField(pk=True) # Overriding 

    # Adding fields
    max_days = fields.SmallIntField(description="最长保存天数", default=7)
    max_times = fields.SmallIntField(description="最大下载次数", default=10)
    error_count = fields.SmallIntField(description="失败次数", default=5)
    error_minute = fields.SmallIntField(description="错误限制分钟数", default=5)
    upload_count = fields.SmallIntField(description="上传次数", default=10)
    upload_minute = fields.SmallIntField(description="上传限制分钟数", default=5)
    upload_file_size = fields.IntField(
        description="上传文件大小 Byte", default=10485760)  # 10M 10*1024*1024

    class Meta:
        table = "settings"

    def __str__(self):
        return self.id     




Set_Pydantic = pydantic_model_creator(Settings, name="Settings")
SetIn_Pydantic = pydantic_model_creator(Settings, name="SettingsIn", exclude=("id", ), exclude_readonly=True)


class ExpiredMixin(Model):
    exp_time = fields.DatetimeField(null=True, description="过期时间")

class Codes(TimestampMixin, ExpiredMixin):
    """Code"""
    id = fields.UUIDField(pk=True, index=True)
    code = fields.CharField(unique=True, max_length=10, index=True)
    key = fields.CharField(max_length=32, unique=True)
    name = fields.CharField(max_length=500, description="分享类型名称")
    size = fields.IntField()
    type = fields.CharField(max_length=200, description="类型")
    text = fields.TextField()
    used = fields.BooleanField(default=False)
    count = fields.IntField(default=-1, description="有效次数")

    class Meta:
        table = "codes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

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
        return ''

    class PydanticMeta:
        computed = ["get_texts", "get_type", "get_short_text"]


Codes_Pydantic = pydantic_model_creator(
    Codes, 
    name="Codes", 
    include=("id", "code", "name", "exp_time", "count", "size"), 
    computed=['get_texts', "get_type", "get_short_text"])

