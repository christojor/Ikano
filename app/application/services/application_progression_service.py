from app.application.domain.exceptions import InvalidStepTransitionError
from app.application.domain.onboarding import ApplicationRecord, OnboardingFlow, OnboardingStep


class ApplicationProgressionService:
    def get_current_step(
        self, application: ApplicationRecord, flow: OnboardingFlow
    ) -> OnboardingStep:
        current_index = application.current_step_order - 1
        if current_index < 0 or current_index >= len(flow.steps):
            raise InvalidStepTransitionError("Current step is out of flow bounds")
        return flow.steps[current_index]

    def has_next_step(self, application: ApplicationRecord, flow: OnboardingFlow) -> bool:
        return application.current_step_order < len(flow.steps)

    def move_to_next_step(self, application: ApplicationRecord, flow: OnboardingFlow) -> None:
        if not self.has_next_step(application, flow):
            raise InvalidStepTransitionError("No next step available")

        next_step = flow.steps[application.current_step_order]
        application.current_step_order = next_step.step_order
        application.current_step_code = next_step.step_code
