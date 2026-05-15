from fastapi import FastAPI

from app.infrastructure.config import settings
from app.presentation.web.routes import router as web_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(web_router)
    return app


app = create_app()
