from typing import Protocol

from app.application.domain.onboarding import CountryCode, OnboardingFlow, PartyTypeCode


class FlowQueryPort(Protocol):
    def get_active_flow(
        self, country_code: CountryCode, party_type_code: PartyTypeCode
    ) -> OnboardingFlow | None: ...

    def get_flow_by_id(self, flow_id: int) -> OnboardingFlow | None: ...
