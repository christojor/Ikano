from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.health_service import HealthService
from app.application.services.onboarding_service import OnboardingService
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.repositories.sqlalchemy_onboarding_repository import (
    SQLAlchemyOnboardingRepository,
)


def get_health_service() -> HealthService:
    return HealthService()


def get_onboarding_service(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> OnboardingService:
    repository = SQLAlchemyOnboardingRepository(session=db_session)
    unit_of_work = SQLAlchemyUnitOfWork(session=db_session)
    return OnboardingService(
        flow_query=repository,
        application_repository=repository,
        audit_repository=repository,
        check_run_repository=repository,
        manual_review_repository=repository,
        unit_of_work=unit_of_work,
    )
