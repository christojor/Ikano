from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from app.application.domain.exceptions import (
    ApplicationNotFoundError,
    InvalidStepPayloadError,
    NoActiveOnboardingFlowError,
    OnboardingFlowNotFoundError,
    UnsupportedCountryCodeError,
    UnsupportedPartyTypeCodeError,
)
from app.application.domain.onboarding import (
    ApplicationRecord,
    ApplicationStepRecord,
    ApplicationStatus,
    AuditEvent,
    CheckRunRecord,
    ManualReviewCaseRecord,
)
from app.application.services.health_service import HealthService
from app.application.services.onboarding_service import OnboardingService
from app.infrastructure.config import settings
from app.presentation.dependencies import get_health_service, get_onboarding_service

router = APIRouter()
WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"

templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

_TERMINAL_STATUSES = {
    ApplicationStatus.APPROVED,
    ApplicationStatus.REJECTED,
    ApplicationStatus.UNDER_REVIEW,
    ApplicationStatus.CANCELLED,
}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class StartApplicationRequest(BaseModel):
    """
    Request to start a new onboarding application.

    Supported country codes: SE, ES, PL
    Supported party types: PRIVATE (individual), BUSINESS (company)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "country_code": "SE",
                "party_type_code": "PRIVATE",
            }
        }
    )

    country_code: str = Field(
        ...,
        description="ISO 3166-1 alpha-2 country code (SE, ES, PL)",
        examples=["SE", "ES", "PL"],
    )
    party_type_code: str = Field(
        ...,
        description="Type of applicant: PRIVATE for individuals, BUSINESS for companies",
        examples=["PRIVATE", "BUSINESS"],
    )


class AdvanceStepRequest(BaseModel):
    """
    Request to advance an application to the next onboarding step.

    The scenario parameter determines the check result:
    - PASS: All checks passed, proceed to next step
    - FAIL: Check failed, application rejected
    - MANUAL_REVIEW: Check requires manual review
    """

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "scenario": "PASS",
                "identity_number": "199001019999",
            }
        }
    )

    scenario: str = Field(
        default="PASS",
        description="Check outcome scenario (PASS, FAIL, or MANUAL_REVIEW)",
        examples=["PASS", "FAIL", "MANUAL_REVIEW"],
    )


class ApplicationResponse(BaseModel):
    """
    Current state of an onboarding application.

    Fields:
    - application_id: Unique internal identifier
    - public_reference: Customer-facing reference (e.g., "APP-000001")
    - status: Current workflow state (IN_PROGRESS, APPROVED, REJECTED, etc.)
    - current_step_code: Name of the current step in the flow
    - current_step_order: Position in the flow (1-indexed)
    """

    application_id: int = Field(..., description="Unique application identifier")
    public_reference: str = Field(
        ..., description="Customer-facing reference ID"
    )
    country_code: str = Field(..., description="Country code (SE, ES, PL)")
    party_type_code: str = Field(
        ..., description="Applicant type (PRIVATE or BUSINESS)"
    )
    status: str = Field(
        ...,
        description="Application status (IN_PROGRESS, APPROVED, REJECTED, UNDER_REVIEW, SUBMITTED, CANCELLED, DRAFT)",
    )
    current_step_code: str = Field(
        ..., description="Code of current step"
    )
    current_step_order: int = Field(
        ..., description="Step position in flow (1-indexed)"
    )
    submitted_at: str | None = Field(
        None,
        description="ISO 8601 timestamp when application was submitted",
    )


class AuditEventResponse(BaseModel):
    """
    Audit trail entry documenting an action or event in the application lifecycle.

    Tracks who did what, when, and in what context (correlation_id links related events).
    """

    application_id: int = Field(..., description="Application being audited")
    event_type: str = Field(
        ...,
        description="Type of event (APPLICATION_STARTED, STEP_COMPLETED, CHECK_COMPLETED, etc.)",
    )
    event_timestamp: str = Field(
        ..., description="When event occurred (ISO 8601)"
    )
    actor_type: str = Field(
        ...,
        description="Who performed the action (SYSTEM, USER, or AGENT)",
    )
    actor_id: str = Field(
        ..., description="Identifier of who performed the action"
    )
    correlation_id: str = Field(
        ...,
        description="Business reference linking related events",
    )
    metadata: dict[str, str] = Field(
        ...,
        description="Additional context (step_code, check_result, etc.)",
    )


class CheckRunResponse(BaseModel):
    """
    Result of a compliance check (KYC, KYB, SANCTIONS, CREDIT, REGISTRY).

    Each check is independently evaluated and recorded with a deterministic result.
    """

    check_run_id: int = Field(..., description="Unique check execution identifier")
    application_id: int = Field(..., description="Application being checked")
    check_type_code: str = Field(
        ...,
        description="Type of check (KYC, KYB, SANCTIONS, CREDIT, REGISTRY)",
    )
    check_business_result_code: str = Field(
        ...,
        description="Check outcome (PASS, FAIL, or MANUAL_REVIEW)",
    )
    correlation_id: str = Field(
        ...,
        description="Reference linking check to application request",
    )
    input_fingerprint: str = Field(
        ...,
        description="Hash of check input (for audit/replay purposes)",
    )
    created_at: str = Field(
        ..., description="When check was executed (ISO 8601)"
    )


class ManualReviewResponse(BaseModel):
    """
    Manual review case opened for an application.

    Used when automated checks cannot definitively approve/reject an applicant.
    """

    manual_review_case_id: int = Field(..., description="Unique case identifier")
    application_id: int = Field(..., description="Application under review")
    review_status: str = Field(
        ...,
        description="Case status (OPEN, IN_REVIEW, ESCALATED, or CLOSED)",
    )
    opened_at: str = Field(
        ..., description="When case was opened (ISO 8601)"
    )


class ApplicationStepResponse(BaseModel):
    """Persisted status trail for completed onboarding steps."""

    application_step_id: int = Field(..., description="Unique step record identifier")
    application_id: int = Field(..., description="Application identifier")
    step_code: str = Field(..., description="Step code completed by the application")
    step_order: int = Field(..., description="Step order within flow")
    step_status_code: str = Field(..., description="Step lifecycle status")
    payload_snapshot: dict[str, str] = Field(..., description="Captured payload submitted at completion")
    completed_at: str = Field(..., description="Completion timestamp (ISO 8601)")


def _to_application_response(application: ApplicationRecord) -> ApplicationResponse:
    """Convert domain ApplicationRecord to API response model."""
    submitted_at = (
        application.submitted_at.isoformat()
        if application.submitted_at is not None
        else None
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


def _to_audit_event_response(event: AuditEvent) -> AuditEventResponse:
    """Convert domain AuditEvent to API response model."""
    return AuditEventResponse(
        application_id=event.application_id,
        event_type=event.event_type.value,
        event_timestamp=event.event_timestamp.isoformat(),
        actor_type=event.actor_type.value,
        actor_id=event.actor_id,
        correlation_id=event.correlation_id,
        metadata=event.metadata,
    )


def _to_check_run_response(check_run: CheckRunRecord) -> CheckRunResponse:
    """Convert domain CheckRunRecord to API response model."""
    return CheckRunResponse(
        check_run_id=check_run.check_run_id,
        application_id=check_run.application_id,
        check_type_code=check_run.check_type_code.value,
        check_business_result_code=check_run.check_business_result_code.value,
        correlation_id=check_run.correlation_id,
        input_fingerprint=check_run.input_fingerprint,
        created_at=check_run.created_at.isoformat(),
    )


def _to_manual_review_response(case: ManualReviewCaseRecord) -> ManualReviewResponse:
    """Convert domain ManualReviewCaseRecord to API response model."""
    return ManualReviewResponse(
        manual_review_case_id=case.manual_review_case_id,
        application_id=case.application_id,
        review_status=case.review_status.value,
        opened_at=case.opened_at.isoformat(),
    )


def _to_application_step_response(step: ApplicationStepRecord) -> ApplicationStepResponse:
    """Convert domain ApplicationStepRecord to API response model."""
    return ApplicationStepResponse(
        application_step_id=step.application_step_id,
        application_id=step.application_id,
        step_code=step.step_code,
        step_order=step.step_order,
        step_status_code=step.step_status_code.value,
        payload_snapshot=step.payload_snapshot,
        completed_at=step.completed_at.isoformat(),
    )


# ============================================================================
# APPLICATION ENDPOINTS
# ============================================================================


@router.get(
    "/",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Home page",
)
def home(
    request: Request,
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> HTMLResponse:
    """
    Render the home page with system health status.

    Displays:
    - Welcome message
    - Navigation to start new application
    - System health indicator
    """
    context = {
        "request": request,
        "status": health_service.get_status(),
        "show_home_service_status": settings.show_home_service_status,
    }
    return templates.TemplateResponse(request, "index.html", context)


@router.post(
    "/api/onboarding/start",
    response_model=ApplicationResponse,
    status_code=201,
    tags=["Applications"],
    summary="Start new application",
    responses={
        201: {"description": "Application created successfully"},
        400: {"description": "Invalid country code, party type, or no active flow for combination"},
    },
)
def start_onboarding(
    payload: StartApplicationRequest,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ApplicationResponse:
    """
    Initiate a new onboarding application.

    Creates an application record, generates a public reference, and initializes the first step.
    A corresponding audit event is recorded.

    Raises:
    - 400: If country/party type not supported or no active flow configured
    """
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


@router.post(
    "/api/onboarding/{application_id}/advance",
    response_model=ApplicationResponse,
    tags=["Applications"],
    summary="Advance to next step",
    responses={
        200: {"description": "Application advanced successfully"},
        404: {"description": "Application not found"},
        400: {"description": "Invalid flow or step transition"},
    },
)
def advance_onboarding(
    application_id: int,
    payload: AdvanceStepRequest,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ApplicationResponse:
    """
    Progress an application to the next step in its onboarding flow.

    Executes compliance checks (KYC, KYB, SANCTIONS, etc.) based on the current step.
    The scenario parameter determines check outcomes:
    - PASS: Proceed to next step
    - FAIL: Mark application as rejected
    - MANUAL_REVIEW: Create manual review case for human decision

    Updates application status and records audit events for all state changes.

    Raises:
    - 404: Application not found
    - 400: Flow not found or invalid step transition
    """
    try:
        extra_payload = {
            key: str(value)
            for key, value in (payload.model_extra or {}).items()
        }
        application = onboarding_service.advance_step(
            application_id=application_id,
            payload={"scenario": payload.scenario, **extra_payload},
        )
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (OnboardingFlowNotFoundError, InvalidStepPayloadError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_application_response(application)


@router.get(
    "/api/onboarding/{application_id}",
    response_model=ApplicationResponse,
    tags=["Applications"],
    summary="Get application status",
    responses={
        200: {"description": "Current application state"},
        404: {"description": "Application not found"},
    },
)
def get_onboarding_application(
    application_id: int,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ApplicationResponse:
    """
    Retrieve the current state of an onboarding application.

    Includes:
    - Current step in the flow
    - Overall status (IN_PROGRESS, APPROVED, REJECTED, etc.)
    - Timestamps and references

    Raises:
    - 404: Application not found
    """
    try:
        application = onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _to_application_response(application)


@router.get(
    "/api/onboarding/{application_id}/steps",
    response_model=list[ApplicationStepResponse],
    tags=["Applications"],
    summary="Get step status trail",
    responses={
        200: {"description": "Persisted step status trail (may be empty)"},
        404: {"description": "Application not found"},
    },
)
def get_application_steps(
    application_id: int,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> list[ApplicationStepResponse]:
    """Retrieve persisted completed step records for the application."""
    try:
        onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    steps = onboarding_service.get_application_steps(application_id=application_id)
    return [_to_application_step_response(step) for step in steps]


# ============================================================================
# AUDIT TRAIL ENDPOINTS
# ============================================================================


@router.get(
    "/api/onboarding/{application_id}/audit-events",
    response_model=list[AuditEventResponse],
    tags=["Audit Trail"],
    summary="Get audit events",
    responses={
        200: {"description": "List of audit trail entries (may be empty)"},
        404: {"description": "Application not found"},
    },
)
def get_audit_events(
    application_id: int,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> list[AuditEventResponse]:
    """
    Retrieve the complete audit trail for an application.

    Includes all recorded events:
    - APPLICATION_STARTED: When application was created
    - STEP_COMPLETED: When user advanced to next step
    - CHECK_COMPLETED: When compliance check was executed
    - APPLICATION_DECIDED: When final decision was made
    - MANUAL_REVIEW_OPENED: When case was escalated for review

    Events are ordered chronologically and include metadata for context.

    Raises:
    - 404: Application not found
    """
    # Verify application exists
    try:
        onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    events = onboarding_service.get_audit_events(application_id=application_id)
    return [_to_audit_event_response(event) for event in events]


# ============================================================================
# COMPLIANCE CHECKS ENDPOINTS
# ============================================================================


@router.get(
    "/api/onboarding/{application_id}/check-runs",
    response_model=list[CheckRunResponse],
    tags=["Compliance Checks"],
    summary="Get check results",
    responses={
        200: {"description": "List of compliance check results (may be empty)"},
        404: {"description": "Application not found"},
    },
)
def get_check_runs(
    application_id: int,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> list[CheckRunResponse]:
    """
    Retrieve all compliance check results for an application.

    Each step in the onboarding flow may include checks:
    - KYC: Know Your Customer check for individual applicants
    - KYB: Know Your Business check for company applicants
    - SANCTIONS: Sanctions screening against international lists
    - CREDIT: Credit history check
    - REGISTRY: Business registry verification

    Checks are recorded with:
    - Input fingerprint (for audit/replay)
    - Deterministic outcome (PASS, FAIL, MANUAL_REVIEW)
    - Execution timestamp

    Raises:
    - 404: Application not found
    """
    # Verify application exists
    try:
        onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    check_runs = onboarding_service.get_check_runs(application_id=application_id)
    return [_to_check_run_response(check_run) for check_run in check_runs]


# ============================================================================
# MANUAL REVIEW ENDPOINTS
# ============================================================================


@router.get(
    "/api/onboarding/{application_id}/manual-review",
    response_model=ManualReviewResponse | None,
    tags=["Manual Review"],
    summary="Get manual review case",
    responses={
        200: {"description": "Manual review case (null if no case exists)"},
        404: {"description": "Application not found"},
    },
)
def get_manual_review(
    application_id: int,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> ManualReviewResponse | None:
    """
    Retrieve the manual review case for an application (if one exists).

    A manual review case is created when:
    - A compliance check returns MANUAL_REVIEW outcome
    - Application requires human judgment for approval/rejection

    Case lifecycle:
    - OPEN: Case created, awaiting assignment
    - IN_REVIEW: Case assigned to reviewer
    - ESCALATED: Case escalated to supervisor
    - CLOSED: Final decision made

    Returns None if no manual review case exists for the application.

    Raises:
    - 404: Application not found
    """
    # Verify application exists
    try:
        onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    case = onboarding_service.get_manual_review_case(application_id=application_id)
    return _to_manual_review_response(case) if case else None


# ============================================================================
# ONBOARDING UI ROUTES (Server-rendered pages)
# ============================================================================


@router.get(
    "/onboarding",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Onboarding start page",
)
def onboarding_start_page(request: Request) -> HTMLResponse:
    """
    Render the onboarding start page.

    Displays form to select:
    - Country (SE, ES, PL)
    - Party type (PRIVATE or BUSINESS)

    Form submission creates a new application via POST /api/onboarding/start.
    """
    return templates.TemplateResponse(request, "onboarding/start.html", {})


@router.get(
    "/onboarding/{application_id}/step",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Onboarding step page",
)
def onboarding_step_page(
    application_id: int,
    request: Request,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> Response:
    """
    Render the current onboarding step page.

    Displays:
    - Step title and description
    - Progress indicator
    - Step-specific form (if applicable)
    - Navigation controls

    Automatically redirects to result page if application is in a terminal status.

    Raises:
    - 404: Application not found
    """
    try:
        application = onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    if application.status in _TERMINAL_STATUSES:
        return RedirectResponse(url=f"/onboarding/{application_id}/result")

    try:
        flow = onboarding_service.get_flow_for_application(application_id=application_id)
    except OnboardingFlowNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    current_step = next(
        (s for s in flow.steps if s.step_order == application.current_step_order),
        flow.steps[0],
    )
    total_steps = len(flow.steps)
    progress_pct = int((application.current_step_order - 1) / total_steps * 100)

    return templates.TemplateResponse(
        request,
        "onboarding/step.html",
        {
            "application": application,
            "step": current_step,
            "total_steps": total_steps,
            "progress_pct": progress_pct,
        },
    )


@router.get(
    "/onboarding/{application_id}/result",
    response_class=HTMLResponse,
    tags=["Pages"],
    summary="Application result page",
)
def onboarding_result_page(
    application_id: int,
    request: Request,
    onboarding_service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> HTMLResponse:
    """
    Render the final result page showing application outcome.

    Displays:
    - Final status (APPROVED, REJECTED, or UNDER_REVIEW)
    - Public reference number
    - Next steps or contact information
    - Option to start new application

    Raises:
    - 404: Application not found
    """
    try:
        application = onboarding_service.get_application(application_id=application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return templates.TemplateResponse(
        request, "onboarding/result.html", {"application": application}
    )

