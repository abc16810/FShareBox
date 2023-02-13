from typing import List

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from apps.models import Settings
from common.utils import get_app_settings

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    print(request)
    a = templates.TemplateResponse("index.html", {"request": request})
    print(a.context)
    return a




