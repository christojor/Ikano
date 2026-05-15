from app.application.services.health_service import HealthService


def get_health_service() -> HealthService:
    return HealthService()
