# coding: utf-8
from typing import Any, Dict, List, Optional

from pydantic import AnyUrl, BaseModel, BaseSettings, RedisDsn, SecretStr


class AppSettings(BaseSettings):
    author: str = "wsm"
    title: str = "FShareBox - 共享快递箱"
    version: str = "1.0"
    description: str = "FShareBox，共享文件快递柜，口令传送箱，匿名口令分享文本，文件，图片"
    keywords: str = "FShareBox，共享文件快递柜，口令传送箱，匿名口令分享文本，文件，图片"

    debug: bool = True

    # 存储引擎：['aliyunsystem','filesystem']
    storage_engine: str = "filesystem"

    openapi_url: Optional[str] = "/openapi.json"
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"

    allowed_hosts: List[str] = ["*"]

    api_prefix: str = "/api"
    api_manager_prefix: str = "/admin"
    api_manager_password: str = "admin@123"
    api_manager_password_expire_minute = 30  # 过期时间

    #  Sqlite数据库文件
    db_file = "db/database.db"
    db_url = f"sqlite:///{db_file}"

    static_url = "/static"

    # 数据存储文件夹，
    data_root = './data'
    # 删除过期文件的间隔（分钟）
    delete_expire_file_interval = 10

    class Config:
        validate_assignment = True  # 是否对属性赋值进行验证
        fields = {
            'version': {
                'env': ['VERSION', 'APP_VERSION']
            },
            'debug': {
                'env': ['DEBUG', 'APP_DEBUG']
            },
            'storage_engine': {
                'env': ['STORAGE_ENGINE']
            },
            'api_manager_password': {
                'env': ['ADMIN_PASSWORD']
            }

        }
        env_file = ".env"  # python-dotenv
        env_file_encoding = 'utf-8'

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        kwargs = {
            "debug": self.debug,
            "title": self.title,
            "version": self.version,
            "description": self.description,
        }
        if not self.debug:
            self.openapi_url, self.docs_url, self.redoc_url = None, None, None
            kwargs["openapi_url"] = self.openapi_url
            kwargs["docs_url"] = self.docs_url
            kwargs["redoc_url"] = self.redoc_url
            return kwargs
        else:
            return kwargs

# settings = Settings(_env_file='prod.env', _env_file_encoding='utf-8')   实例化优先于Config
# settings = Settings(_env_file=None) 不加载任何变量文件
