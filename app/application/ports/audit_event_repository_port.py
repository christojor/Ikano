from typing import Protocol

from app.application.domain.onboarding import AuditEvent


class AuditEventRepositoryPort(Protocol):
    def append_audit_event(self, event: AuditEvent) -> None: ...

    def list_audit_events(self, application_id: int) -> tuple[AuditEvent, ...]: ...
