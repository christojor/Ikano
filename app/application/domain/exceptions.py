class OnboardingError(Exception):
    """Base domain exception for onboarding use cases."""


class UnsupportedCountryCodeError(OnboardingError):
    pass


class UnsupportedPartyTypeCodeError(OnboardingError):
    pass


class ApplicationNotFoundError(OnboardingError):
    pass


class NoActiveOnboardingFlowError(OnboardingError):
    pass


class OnboardingFlowNotFoundError(OnboardingError):
    pass


class InvalidStepTransitionError(OnboardingError):
    pass


class InvalidStepPayloadError(OnboardingError):
    pass
