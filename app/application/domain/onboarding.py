from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CountryCode(StrEnum):
    SE = "SE"
    ES = "ES"
    PL = "PL"


class PartyTypeCode(StrEnum):
    PRIVATE = "PRIVATE"
    BUSINESS = "BUSINESS"


class ApplicationStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class StepStatusCode(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class CheckTypeCode(StrEnum):
    KYC = "KYC"
    KYB = "KYB"
    SANCTIONS = "SANCTIONS"
    CREDIT = "CREDIT"
    REGISTRY = "REGISTRY"


class CheckBusinessResultCode(StrEnum):
    PASS = "PASS"  # nosec B105
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FAIL = "FAIL"


class CheckTechnicalResultCode(StrEnum):
    OK = "OK"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class DecisionOutcomeCode(StrEnum):
    APPROVED = "APPROVED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"


@dataclass(slots=True, frozen=True)
class CheckEvaluationResult:
    check_business_result_code: CheckBusinessResultCode
    check_technical_result_code: CheckTechnicalResultCode
    adapter_name: str
    outcome_reason_code: str


@dataclass(slots=True, frozen=True)
class DecisionResult:
    outcome_code: DecisionOutcomeCode
    reason_codes: tuple[str, ...]
    rule_version: str
    explanation: dict[str, str]


class ManualReviewStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class ActorType(StrEnum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    AGENT = "AGENT"


class AuditEventType(StrEnum):
    APPLICATION_STARTED = "APPLICATION_STARTED"
    STEP_COMPLETED = "STEP_COMPLETED"
    CHECK_COMPLETED = "CHECK_COMPLETED"
    APPLICATION_DECIDED = "APPLICATION_DECIDED"
    MANUAL_REVIEW_OPENED = "MANUAL_REVIEW_OPENED"


@dataclass(slots=True, frozen=True)
class OnboardingStep:
    step_code: str
    step_title: str
    step_order: int
    check_type_code: CheckTypeCode | None = None


@dataclass(slots=True, frozen=True)
class OnboardingFlow:
    flow_id: int
    country_code: CountryCode
    party_type_code: PartyTypeCode
    steps: tuple[OnboardingStep, ...]
    is_active: bool = True


@dataclass(slots=True)
class ApplicationRecord:
    application_id: int
    public_reference: str
    country_code: CountryCode
    party_type_code: PartyTypeCode
    flow_id: int
    current_step_order: int
    current_step_code: str
    status: ApplicationStatus
    created_at: datetime
    submitted_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class ApplicationStepRecord:
    application_step_id: int
    application_id: int
    step_code: str
    step_order: int
    step_status_code: StepStatusCode
    payload_snapshot: dict[str, str]
    completed_at: datetime


@dataclass(slots=True, frozen=True)
class AuditEvent:
    application_id: int
    event_type: AuditEventType
    event_timestamp: datetime
    actor_type: ActorType
    actor_id: str
    correlation_id: str
    metadata: dict[str, str]


@dataclass(slots=True, frozen=True)
class CheckRunRecord:
    check_run_id: int
    application_id: int
    check_type_code: CheckTypeCode
    check_business_result_code: CheckBusinessResultCode
    correlation_id: str
    input_fingerprint: str
    created_at: datetime


@dataclass(slots=True, frozen=True)
class ManualReviewCaseRecord:
    manual_review_case_id: int
    application_id: int
    review_status: ManualReviewStatus
    opened_at: datetime
