from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.application.services.health_service import HealthService
from app.presentation.dependencies import get_health_service

router = APIRouter()

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent / "templates")
)


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> HTMLResponse:
    context = {
        "request": request,
        "status": health_service.get_status(),
    }
    return templates.TemplateResponse(request, "index.html", context)
