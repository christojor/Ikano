from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.application.services.onboarding_service import OnboardingService
from app.infrastructure.repositories.in_memory_onboarding_repository import (
    InMemoryOnboardingRepository,
)
from app.main import app
from app.presentation.dependencies import get_onboarding_service


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    repository = InMemoryOnboardingRepository()
    service = OnboardingService(
        flow_query=repository,
        application_repository=repository,
        audit_repository=repository,
        check_run_repository=repository,
        manual_review_repository=repository,
    )

    app.dependency_overrides[get_onboarding_service] = lambda: service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
