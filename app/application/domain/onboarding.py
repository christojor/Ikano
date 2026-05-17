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
    PASS = "PASS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FAIL = "FAIL"


class DecisionOutcomeCode(StrEnum):
    APPROVED = "APPROVED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"


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
