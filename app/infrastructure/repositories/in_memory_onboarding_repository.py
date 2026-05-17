from app.application.domain.onboarding import (
    ApplicationRecord,
    AuditEvent,
    CheckRunRecord,
    CheckTypeCode,
    CountryCode,
    ManualReviewCaseRecord,
    OnboardingFlow,
    OnboardingStep,
    PartyTypeCode,
)


class InMemoryOnboardingRepository:
    def __init__(self) -> None:
        self._flows = self._build_default_flows()
        self._applications: dict[int, ApplicationRecord] = {}
        self._audit_events: dict[int, list[AuditEvent]] = {}
        self._check_runs: dict[int, list[CheckRunRecord]] = {}
        self._manual_review_cases: dict[int, ManualReviewCaseRecord] = {}
        self._application_counter = 0
        self._check_run_counter = 0
        self._manual_review_counter = 0

    def _build_default_flows(self) -> dict[tuple[CountryCode, PartyTypeCode], OnboardingFlow]:
        flows: dict[tuple[CountryCode, PartyTypeCode], OnboardingFlow] = {}
        flow_id = 0
        for country_code in CountryCode:
            flow_id += 1
            flows[(country_code, PartyTypeCode.PRIVATE)] = OnboardingFlow(
                flow_id=flow_id,
                country_code=country_code,
                party_type_code=PartyTypeCode.PRIVATE,
                steps=(
                    OnboardingStep("COLLECT_PRIVATE_PROFILE", "Collect applicant profile", 1),
                    OnboardingStep(
                        "RUN_KYC", "Run KYC check", 2, check_type_code=CheckTypeCode.KYC
                    ),
                    OnboardingStep(
                        "RUN_SANCTIONS",
                        "Run sanctions screening",
                        3,
                        check_type_code=CheckTypeCode.SANCTIONS,
                    ),
                    OnboardingStep("DECISION", "Apply decision rules", 4),
                ),
            )

            flow_id += 1
            flows[(country_code, PartyTypeCode.BUSINESS)] = OnboardingFlow(
                flow_id=flow_id,
                country_code=country_code,
                party_type_code=PartyTypeCode.BUSINESS,
                steps=(
                    OnboardingStep("COLLECT_BUSINESS_PROFILE", "Collect business profile", 1),
                    OnboardingStep(
                        "RUN_KYB", "Run KYB check", 2, check_type_code=CheckTypeCode.KYB
                    ),
                    OnboardingStep(
                        "RUN_REGISTRY",
                        "Run business registry check",
                        3,
                        check_type_code=CheckTypeCode.REGISTRY,
                    ),
                    OnboardingStep("DECISION", "Apply decision rules", 4),
                ),
            )
        return flows

    def get_active_flow(
        self, country_code: CountryCode, party_type_code: PartyTypeCode
    ) -> OnboardingFlow | None:
        return self._flows.get((country_code, party_type_code))

    def get_flow_by_id(self, flow_id: int) -> OnboardingFlow | None:
        for flow in self._flows.values():
            if flow.flow_id == flow_id:
                return flow
        return None

    def create_application(self, application: ApplicationRecord) -> ApplicationRecord:
        self._applications[application.application_id] = application
        return application

    def get_application(self, application_id: int) -> ApplicationRecord | None:
        return self._applications.get(application_id)

    def update_application(self, application: ApplicationRecord) -> None:
        self._applications[application.application_id] = application

    def next_application_id(self) -> int:
        self._application_counter += 1
        return self._application_counter

    def append_audit_event(self, event: AuditEvent) -> None:
        self._audit_events.setdefault(event.application_id, []).append(event)

    def list_audit_events(self, application_id: int) -> tuple[AuditEvent, ...]:
        return tuple(self._audit_events.get(application_id, []))

    def next_check_run_id(self) -> int:
        self._check_run_counter += 1
        return self._check_run_counter

    def append_check_run(self, check_run: CheckRunRecord) -> None:
        self._check_runs.setdefault(check_run.application_id, []).append(check_run)

    def list_check_runs(self, application_id: int) -> tuple[CheckRunRecord, ...]:
        return tuple(self._check_runs.get(application_id, []))

    def next_manual_review_case_id(self) -> int:
        self._manual_review_counter += 1
        return self._manual_review_counter

    def create_manual_review_case(self, case: ManualReviewCaseRecord) -> ManualReviewCaseRecord:
        self._manual_review_cases[case.application_id] = case
        return case

    def get_manual_review_case(self, application_id: int) -> ManualReviewCaseRecord | None:
        return self._manual_review_cases.get(application_id)
