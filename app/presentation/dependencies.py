from functools import lru_cache

from app.application.services.health_service import HealthService
from app.application.services.onboarding_service import OnboardingService
from app.infrastructure.repositories.in_memory_onboarding_repository import (
    InMemoryOnboardingRepository,
)


def get_health_service() -> HealthService:
    return HealthService()


@lru_cache
def get_onboarding_repository() -> InMemoryOnboardingRepository:
    return InMemoryOnboardingRepository()


def get_onboarding_service() -> OnboardingService:
    repository = get_onboarding_repository()
    return OnboardingService(
        flow_query=repository,
        application_repository=repository,
        audit_repository=repository,
        check_run_repository=repository,
        manual_review_repository=repository,
    )
