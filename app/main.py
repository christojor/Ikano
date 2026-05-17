from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.infrastructure.config import settings
from app.presentation.web.routes import STATIC_DIR
from app.presentation.web.routes import router as web_router

# OpenAPI tags for Swagger UI organization
OPENAPI_TAGS = [
    {
        "name": "Applications",
        "description": "Onboarding application lifecycle management. Start, advance, and retrieve application status.",
    },
    {
        "name": "Audit Trail",
        "description": "Audit events and activity tracking. Access the complete history of actions taken on an application.",
    },
    {
        "name": "Compliance Checks",
        "description": "KYC/KYB compliance check results. View check outcomes and audit records.",
    },
    {
        "name": "Manual Review",
        "description": "Manual review cases. Access and manage applications requiring human review.",
    },
    {
        "name": "Pages",
        "description": "Server-rendered HTML pages for the user interface.",
    },
]


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Includes:
    - API routes for onboarding operations
    - Static file serving for CSS, JS, and images
    - OpenAPI/Swagger documentation with tags and descriptions
    - Request/response validation via Pydantic models
    """
    app = FastAPI(
        title="Ikano Bank Onboarding API",
        description=(
            "Comprehensive KYC/KYB onboarding API for Ikano Bank. "
            "Manages multi-country onboarding flows for private and business applicants. "
            "Includes compliance checks, decision rules, audit trails, and manual review workflows."
        ),
        version="1.0.0",
        openapi_tags=OPENAPI_TAGS,
        debug=settings.debug,
    )
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
