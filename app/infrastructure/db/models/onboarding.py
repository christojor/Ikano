from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base


class CountryModel(Base):
    __tablename__ = "country"

    country_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    country_name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class PartyTypeModel(Base):
    __tablename__ = "party_type"

    party_type_code: Mapped[str] = mapped_column(String(16), primary_key=True)
    description: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class ApplicationStatusModel(Base):
    __tablename__ = "application_status"

    application_status_code: Mapped[str] = mapped_column(String(24), primary_key=True)
    description: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)


class StepStatusModel(Base):
    __tablename__ = "step_status"

    step_status_code: Mapped[str] = mapped_column(String(24), primary_key=True)
    description: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)


class CheckTypeModel(Base):
    __tablename__ = "check_type"

    check_type_code: Mapped[str] = mapped_column(String(24), primary_key=True)
    description: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)


class CheckBusinessResultModel(Base):
    __tablename__ = "check_business_result"

    check_business_result_code: Mapped[str] = mapped_column(String(24), primary_key=True)
    description: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)


class DecisionOutcomeModel(Base):
    __tablename__ = "decision_outcome"

    decision_outcome_code: Mapped[str] = mapped_column(String(24), primary_key=True)
    description: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)


class OnboardingFlowModel(Base):
    __tablename__ = "onboarding_flow"

    flow_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(ForeignKey("country.country_code"), nullable=False)
    party_type_code: Mapped[str] = mapped_column(
        ForeignKey("party_type.party_type_code"), nullable=False
    )
    flow_name: Mapped[str] = mapped_column(String(120), nullable=False)
    flow_version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    steps: Mapped[list["OnboardingStepModel"]] = relationship(
        back_populates="flow",
        cascade="all, delete-orphan",
        order_by="OnboardingStepModel.step_order",
    )

    __table_args__ = (UniqueConstraint("country_code", "party_type_code", "flow_version"),)


class OnboardingStepModel(Base):
    __tablename__ = "onboarding_step"

    step_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    flow_id: Mapped[int] = mapped_column(ForeignKey("onboarding_flow.flow_id"), nullable=False)
    step_code: Mapped[str] = mapped_column(String(32), nullable=False)
    step_title: Mapped[str] = mapped_column(String(120), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    check_type_code: Mapped[str | None] = mapped_column(
        ForeignKey("check_type.check_type_code"), nullable=True
    )

    flow: Mapped[OnboardingFlowModel] = relationship(back_populates="steps")

    __table_args__ = (
        UniqueConstraint("flow_id", "step_code"),
        UniqueConstraint("flow_id", "step_order"),
    )


class ApplicationModel(Base):
    __tablename__ = "application"

    application_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_reference: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    country_code: Mapped[str] = mapped_column(ForeignKey("country.country_code"), nullable=False)
    party_type_code: Mapped[str] = mapped_column(
        ForeignKey("party_type.party_type_code"), nullable=False
    )
    flow_id: Mapped[int] = mapped_column(ForeignKey("onboarding_flow.flow_id"), nullable=False)
    application_status_code: Mapped[str] = mapped_column(
        ForeignKey("application_status.application_status_code"), nullable=False
    )
    current_step_id: Mapped[int | None] = mapped_column(
        ForeignKey("onboarding_step.step_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CheckRunModel(Base):
    __tablename__ = "check_run"

    check_run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("application.application_id"), nullable=False
    )
    check_type_code: Mapped[str] = mapped_column(
        ForeignKey("check_type.check_type_code"), nullable=False
    )
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    check_business_result_code: Mapped[str | None] = mapped_column(
        ForeignKey("check_business_result.check_business_result_code"), nullable=True
    )


class ManualReviewCaseModel(Base):
    __tablename__ = "manual_review_case"

    manual_review_case_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("application.application_id"), nullable=False, unique=True
    )
    review_status: Mapped[str] = mapped_column(String(24), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuditEventModel(Base):
    __tablename__ = "audit_event"

    audit_event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("application.application_id"), nullable=False
    )
    actor_type: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    metadata_json: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
