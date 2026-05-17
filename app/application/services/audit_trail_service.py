from datetime import datetime
import json

from app.application.domain.onboarding import ActorType, AuditEvent, AuditEventType
from app.application.ports.audit_event_repository_port import AuditEventRepositoryPort


class AuditTrailService:
    def __init__(self, audit_repository: AuditEventRepositoryPort) -> None:
        self._audit_repository = audit_repository

    def application_started(
        self,
        *,
        application_id: int,
        correlation_id: str,
        event_timestamp: datetime,
        country_code: str,
        party_type_code: str,
        step_code: str,
    ) -> None:
        self._append(
            application_id=application_id,
            event_type=AuditEventType.APPLICATION_STARTED,
            correlation_id=correlation_id,
            event_timestamp=event_timestamp,
            metadata={
                "country_code": country_code,
                "party_type_code": party_type_code,
                "step_code": step_code,
            },
        )

    def step_completed(
        self,
        *,
        application_id: int,
        correlation_id: str,
        event_timestamp: datetime,
        step_code: str,
    ) -> None:
        self._append(
            application_id=application_id,
            event_type=AuditEventType.STEP_COMPLETED,
            correlation_id=correlation_id,
            event_timestamp=event_timestamp,
            metadata={"step_code": step_code},
        )

    def check_completed(
        self,
        *,
        application_id: int,
        correlation_id: str,
        event_timestamp: datetime,
        check_type_code: str,
        check_business_result_code: str,
        check_technical_result_code: str,
        adapter_name: str,
        outcome_reason_code: str,
    ) -> None:
        self._append(
            application_id=application_id,
            event_type=AuditEventType.CHECK_COMPLETED,
            correlation_id=correlation_id,
            event_timestamp=event_timestamp,
            metadata={
                "check_type_code": check_type_code,
                "check_business_result_code": check_business_result_code,
                "check_technical_result_code": check_technical_result_code,
                "adapter_name": adapter_name,
                "outcome_reason_code": outcome_reason_code,
            },
        )

    def application_decided(
        self,
        *,
        application_id: int,
        correlation_id: str,
        event_timestamp: datetime,
        decision_outcome: str,
        reason_codes: tuple[str, ...],
        rule_version: str,
        explanation: dict[str, str],
    ) -> None:
        self._append(
            application_id=application_id,
            event_type=AuditEventType.APPLICATION_DECIDED,
            correlation_id=correlation_id,
            event_timestamp=event_timestamp,
            metadata={
                "decision_outcome": decision_outcome,
                "reason_codes": ",".join(reason_codes),
                "rule_version": rule_version,
                "explanation_json": json.dumps(explanation, sort_keys=True),
            },
        )

    def manual_review_opened(
        self,
        *,
        application_id: int,
        correlation_id: str,
        event_timestamp: datetime,
        review_status: str,
    ) -> None:
        self._append(
            application_id=application_id,
            event_type=AuditEventType.MANUAL_REVIEW_OPENED,
            correlation_id=correlation_id,
            event_timestamp=event_timestamp,
            metadata={"review_status": review_status},
        )

    def _append(
        self,
        *,
        application_id: int,
        event_type: AuditEventType,
        correlation_id: str,
        event_timestamp: datetime,
        metadata: dict[str, str],
    ) -> None:
        self._audit_repository.append_audit_event(
            AuditEvent(
                application_id=application_id,
                event_type=event_type,
                event_timestamp=event_timestamp,
                actor_type=ActorType.SYSTEM,
                actor_id="onboarding_service",
                correlation_id=correlation_id,
                metadata=metadata,
            )
        )
