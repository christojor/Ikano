from typing import Protocol

from app.application.ports.application_repository_port import ApplicationRepositoryPort
from app.application.ports.audit_event_repository_port import AuditEventRepositoryPort
from app.application.ports.check_run_repository_port import CheckRunRepositoryPort
from app.application.ports.flow_query_port import FlowQueryPort
from app.application.ports.manual_review_repository_port import ManualReviewRepositoryPort


class OnboardingRepository(
    FlowQueryPort,
    ApplicationRepositoryPort,
    AuditEventRepositoryPort,
    CheckRunRepositoryPort,
    ManualReviewRepositoryPort,
    Protocol,
):
    pass
