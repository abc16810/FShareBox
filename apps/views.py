from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from common.utils import get_app_settings

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, set=Depends(get_app_settings)):
    return templates.TemplateResponse(
        "index.html", 
        context={
            "request": request,
            "des": set.description,
            "title": set.title,
            "keywords": set.keywords
        },
        media_type="text/html"
        )

