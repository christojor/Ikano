from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.infrastructure.config import settings
from app.presentation.web.routes import STATIC_DIR
from app.presentation.web.routes import router as web_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
