from dataclasses import dataclass


@dataclass(slots=True)
class HealthService:
    def get_status(self) -> dict[str, str]:
        return {"status": "ok", "service": "onboarding-work-sample"}
