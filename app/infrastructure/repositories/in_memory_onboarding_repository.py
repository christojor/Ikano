from app.application.domain.onboarding import (
    ApplicationRecord,
    ApplicationStepRecord,
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
        self._application_steps: dict[int, list[ApplicationStepRecord]] = {}
        self._audit_events: dict[int, list[AuditEvent]] = {}
        self._check_runs: dict[int, list[CheckRunRecord]] = {}
        self._manual_review_cases: dict[int, ManualReviewCaseRecord] = {}
        self._counters = {
            "application": 0,
            "application_step": 0,
            "check_run": 0,
            "manual_review": 0,
        }

    def _build_default_flows(self) -> dict[tuple[CountryCode, PartyTypeCode], OnboardingFlow]:
        flows: dict[tuple[CountryCode, PartyTypeCode], OnboardingFlow] = {}
        flow_id = 0
        for country_code in CountryCode:
            flow_id += 1
            private_steps: tuple[OnboardingStep, ...]
            if country_code == CountryCode.SE:
                private_steps = (
                    OnboardingStep(
                        "COLLECT_SE_IDENTITY",
                        "Collect personal identity number",
                        1,
                    ),
                    OnboardingStep(
                        "RUN_SE_BANKID",
                        "Run BankID-style identity verification",
                        2,
                        check_type_code=CheckTypeCode.KYC,
                    ),
                    OnboardingStep(
                        "CONFIRM_SE_CONTACT",
                        "Confirm contact details and address",
                        3,
                    ),
                    OnboardingStep(
                        "CAPTURE_SE_CONSENT",
                        "Capture consent, PEP/sanctions, and tax residency",
                        4,
                        check_type_code=CheckTypeCode.SANCTIONS,
                    ),
                    OnboardingStep(
                        "COLLECT_SE_AFFORD",
                        "Collect employment, income, and affordability inputs",
                        5,
                    ),
                    OnboardingStep(
                        "RUN_SE_CREDIT",
                        "Run credit bureau and affordability decision",
                        6,
                        check_type_code=CheckTypeCode.CREDIT,
                    ),
                    OnboardingStep(
                        "REVIEW_SE_SUBMIT",
                        "Review summary, accept terms, and submit",
                        7,
                    ),
                )
            elif country_code == CountryCode.ES:
                private_steps = (
                    OnboardingStep(
                        "COLLECT_ES_DNI_NIE",
                        "Collect DNI/NIE",
                        1,
                    ),
                    OnboardingStep(
                        "RUN_ES_IDENTITY",
                        "Run Clave/DNIe document verification",
                        2,
                        check_type_code=CheckTypeCode.KYC,
                    ),
                    OnboardingStep(
                        "CONFIRM_ES_CONTACT",
                        "Confirm contact details, province, and address",
                        3,
                    ),
                    OnboardingStep(
                        "CAPTURE_ES_CONSENT",
                        "Capture consent and PEP/sanctions declaration",
                        4,
                        check_type_code=CheckTypeCode.SANCTIONS,
                    ),
                    OnboardingStep(
                        "COLLECT_ES_AFFORD",
                        "Collect employment, income, housing costs, and dependants",
                        5,
                    ),
                    OnboardingStep(
                        "RUN_ES_CREDIT",
                        "Run credit bureau and affordability decision",
                        6,
                        check_type_code=CheckTypeCode.CREDIT,
                    ),
                    OnboardingStep(
                        "REVIEW_ES_SUBMIT",
                        "Review summary, accept terms, and submit",
                        7,
                    ),
                )
            else:
                private_steps = (
                    OnboardingStep(
                        "COLLECT_PL_PESEL",
                        "Collect PESEL",
                        1,
                    ),
                    OnboardingStep(
                        "RUN_PL_EID",
                        "Run eID-style identity verification",
                        2,
                        check_type_code=CheckTypeCode.KYC,
                    ),
                    OnboardingStep(
                        "CONFIRM_PL_CONTACT",
                        "Confirm contact details and registered address",
                        3,
                    ),
                    OnboardingStep(
                        "CAPTURE_PL_CONSENT",
                        "Capture consent and PEP/sanctions declaration",
                        4,
                        check_type_code=CheckTypeCode.SANCTIONS,
                    ),
                    OnboardingStep(
                        "COLLECT_PL_AFFORD",
                        "Collect employment, income, and affordability inputs",
                        5,
                    ),
                    OnboardingStep(
                        "RUN_PL_BIK",
                        "Run BIK-style credit bureau and affordability decision",
                        6,
                        check_type_code=CheckTypeCode.CREDIT,
                    ),
                    OnboardingStep(
                        "REVIEW_PL_SUBMIT",
                        "Review summary, accept terms, and submit",
                        7,
                    ),
                )

            flows[(country_code, PartyTypeCode.PRIVATE)] = OnboardingFlow(
                flow_id=flow_id,
                country_code=country_code,
                party_type_code=PartyTypeCode.PRIVATE,
                steps=private_steps,
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
        return self._next_counter("application")

    def next_application_step_id(self) -> int:
        return self._next_counter("application_step")

    def append_application_step(self, application_step: ApplicationStepRecord) -> None:
        self._application_steps.setdefault(application_step.application_id, []).append(application_step)

    def list_application_steps(self, application_id: int) -> tuple[ApplicationStepRecord, ...]:
        return tuple(self._application_steps.get(application_id, []))

    def append_audit_event(self, event: AuditEvent) -> None:
        self._audit_events.setdefault(event.application_id, []).append(event)

    def list_audit_events(self, application_id: int) -> tuple[AuditEvent, ...]:
        return tuple(self._audit_events.get(application_id, []))

    def next_check_run_id(self) -> int:
        return self._next_counter("check_run")

    def append_check_run(self, check_run: CheckRunRecord) -> None:
        self._check_runs.setdefault(check_run.application_id, []).append(check_run)

    def list_check_runs(self, application_id: int) -> tuple[CheckRunRecord, ...]:
        return tuple(self._check_runs.get(application_id, []))

    def next_manual_review_case_id(self) -> int:
        return self._next_counter("manual_review")

    def create_manual_review_case(self, case: ManualReviewCaseRecord) -> ManualReviewCaseRecord:
        self._manual_review_cases[case.application_id] = case
        return case

    def get_manual_review_case(self, application_id: int) -> ManualReviewCaseRecord | None:
        return self._manual_review_cases.get(application_id)

    def _next_counter(self, key: str) -> int:
        self._counters[key] += 1
        return self._counters[key]
