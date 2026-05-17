from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.application.domain.exceptions import (
    ApplicationNotFoundError,
    NoActiveOnboardingFlowError,
    OnboardingFlowNotFoundError,
    UnsupportedCountryCodeError,
    UnsupportedPartyTypeCodeError,
)
from app.application.domain.onboarding import ApplicationRecord
from app.application.services.health_service import HealthService
from app.application.services.onboarding_service import OnboardingService
from app.presentation.dependencies import get_health_service, get_onboarding_service

router = APIRouter()
WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"

templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


class StartApplicationRequest(BaseModel):
    country_code: str
    party_type_code: str


class AdvanceStepRequest(BaseModel):
    scenario: str = "PASS"


class ApplicationResponse(BaseModel):
    application_id: int
    public_reference: str
    country_code: str
    party_type_code: str
    status: str
    current_step_code: str
    current_step_order: int
    submitted_at: str | None


def _to_application_response(application: ApplicationRecord) -> ApplicationResponse:
    submitted_at = (
        application.submitted_at.isoformat() if application.submitted_at is not None else None
    )
    return ApplicationResponse(
        application_id=application.application_id,
        public_reference=application.public_reference,
        country_code=application.country_code.value,
        party_type_code=application.party_type_code.value,
        status=application.status.value,
        current_step_code=application.current_step_code,
        current_step_order=application.current_step_order,
        submitted_at=submitted_at,
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


@router.post("/api/onboarding/start", response_model=ApplicationResponse, status_code=201)
def start_onboarding(
    payload: StartApplicationRequest,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ApplicationResponse:
    try:
        application = onboarding_service.start_application(
            country_code=payload.country_code,
            party_type_code=payload.party_type_code,
        )
    except (
        UnsupportedCountryCodeError,
        UnsupportedPartyTypeCodeError,
        NoActiveOnboardingFlowError,
    ) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_application_response(application)


@router.post("/api/onboarding/{application_id}/advance", response_model=ApplicationResponse)
def advance_onboarding(
    application_id: int,
    payload: AdvanceStepRequest,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ApplicationResponse:
    try:
        application = onboarding_service.advance_step(
            application_id=application_id,
            payload={"scenario": payload.scenario},
        )
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except OnboardingFlowNotFoundError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_application_response(application)


@router.get("/api/onboarding/{application_id}", response_model=ApplicationResponse)
def get_onboarding_application(
    application_id: int,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ApplicationResponse:
    try:
        application = onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _to_application_response(application)
