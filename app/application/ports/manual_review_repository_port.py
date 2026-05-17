from typing import Protocol

from app.application.domain.onboarding import ManualReviewCaseRecord


class ManualReviewRepositoryPort(Protocol):
    def next_manual_review_case_id(self) -> int: ...

    def create_manual_review_case(self, case: ManualReviewCaseRecord) -> ManualReviewCaseRecord: ...

    def get_manual_review_case(self, application_id: int) -> ManualReviewCaseRecord | None: ...
