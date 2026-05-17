"""create onboarding schema and seed data

Revision ID: 20260517_01
Revises:
Create Date: 2026-05-17 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260517_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
    )

    op.create_table(
        "country",
        sa.Column("country_code", sa.String(length=2), primary_key=True),
        sa.Column("country_name", sa.String(length=64), nullable=False, unique=True),
    )
    op.create_table(
        "party_type",
        sa.Column("party_type_code", sa.String(length=16), primary_key=True),
        sa.Column("description", sa.String(length=64), nullable=False, unique=True),
    )
    op.create_table(
        "application_status",
        sa.Column("application_status_code", sa.String(length=24), primary_key=True),
        sa.Column("description", sa.String(length=96), nullable=False, unique=True),
    )
    op.create_table(
        "step_status",
        sa.Column("step_status_code", sa.String(length=24), primary_key=True),
        sa.Column("description", sa.String(length=96), nullable=False, unique=True),
    )
    op.create_table(
        "check_type",
        sa.Column("check_type_code", sa.String(length=24), primary_key=True),
        sa.Column("description", sa.String(length=96), nullable=False, unique=True),
    )
    op.create_table(
        "check_business_result",
        sa.Column("check_business_result_code", sa.String(length=24), primary_key=True),
        sa.Column("description", sa.String(length=96), nullable=False, unique=True),
    )
    op.create_table(
        "decision_outcome",
        sa.Column("decision_outcome_code", sa.String(length=24), primary_key=True),
        sa.Column("description", sa.String(length=96), nullable=False, unique=True),
    )

    op.create_table(
        "onboarding_flow",
        sa.Column("flow_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=2), sa.ForeignKey("country.country_code"), nullable=False),
        sa.Column(
            "party_type_code",
            sa.String(length=16),
            sa.ForeignKey("party_type.party_type_code"),
            nullable=False,
        ),
        sa.Column("flow_name", sa.String(length=120), nullable=False),
        sa.Column("flow_version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("country_code", "party_type_code", "flow_version"),
    )

    op.create_table(
        "onboarding_step",
        sa.Column("step_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("flow_id", sa.BigInteger(), sa.ForeignKey("onboarding_flow.flow_id"), nullable=False),
        sa.Column("step_code", sa.String(length=32), nullable=False),
        sa.Column("step_title", sa.String(length=120), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column(
            "check_type_code",
            sa.String(length=24),
            sa.ForeignKey("check_type.check_type_code"),
            nullable=True,
        ),
        sa.UniqueConstraint("flow_id", "step_code"),
        sa.UniqueConstraint("flow_id", "step_order"),
    )

    op.create_table(
        "application",
        sa.Column("application_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("public_reference", sa.String(length=40), nullable=False, unique=True),
        sa.Column("country_code", sa.String(length=2), sa.ForeignKey("country.country_code"), nullable=False),
        sa.Column(
            "party_type_code",
            sa.String(length=16),
            sa.ForeignKey("party_type.party_type_code"),
            nullable=False,
        ),
        sa.Column("flow_id", sa.BigInteger(), sa.ForeignKey("onboarding_flow.flow_id"), nullable=False),
        sa.Column(
            "application_status_code",
            sa.String(length=24),
            sa.ForeignKey("application_status.application_status_code"),
            nullable=False,
        ),
        sa.Column("current_step_id", sa.BigInteger(), sa.ForeignKey("onboarding_step.step_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "check_run",
        sa.Column("check_run_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("application.application_id"), nullable=False),
        sa.Column("check_type_code", sa.String(length=24), sa.ForeignKey("check_type.check_type_code"), nullable=False),
        sa.Column("correlation_id", sa.String(length=80), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "check_business_result_code",
            sa.String(length=24),
            sa.ForeignKey("check_business_result.check_business_result_code"),
            nullable=True,
        ),
    )

    op.create_table(
        "manual_review_case",
        sa.Column("manual_review_case_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "application_id",
            sa.BigInteger(),
            sa.ForeignKey("application.application_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("review_status", sa.String(length=24), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "audit_event",
        sa.Column("audit_event_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("application.application_id"), nullable=False),
        sa.Column("actor_type", sa.String(length=24), nullable=False),
        sa.Column("actor_id", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("correlation_id", sa.String(length=80), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )

    _seed_lookup_tables()
    _seed_onboarding_flows()


def _seed_lookup_tables() -> None:
    op.bulk_insert(
        sa.table(
            "country",
            sa.column("country_code", sa.String),
            sa.column("country_name", sa.String),
        ),
        [
            {"country_code": "SE", "country_name": "Sweden"},
            {"country_code": "ES", "country_name": "Spain"},
            {"country_code": "PL", "country_name": "Poland"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "party_type",
            sa.column("party_type_code", sa.String),
            sa.column("description", sa.String),
        ),
        [
            {"party_type_code": "PRIVATE", "description": "Private individual"},
            {"party_type_code": "BUSINESS", "description": "Business customer"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "application_status",
            sa.column("application_status_code", sa.String),
            sa.column("description", sa.String),
        ),
        [
            {"application_status_code": "DRAFT", "description": "Application started but not submitted"},
            {"application_status_code": "IN_PROGRESS", "description": "Application is being processed"},
            {"application_status_code": "SUBMITTED", "description": "Application submitted"},
            {"application_status_code": "UNDER_REVIEW", "description": "Application under manual review"},
            {"application_status_code": "APPROVED", "description": "Application approved"},
            {"application_status_code": "REJECTED", "description": "Application rejected"},
            {"application_status_code": "CANCELLED", "description": "Application cancelled"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "step_status",
            sa.column("step_status_code", sa.String),
            sa.column("description", sa.String),
        ),
        [
            {"step_status_code": "NOT_STARTED", "description": "Step has not been started"},
            {"step_status_code": "IN_PROGRESS", "description": "Step is currently active"},
            {"step_status_code": "COMPLETED", "description": "Step completed successfully"},
            {"step_status_code": "SKIPPED", "description": "Step skipped"},
            {"step_status_code": "FAILED", "description": "Step failed"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "check_type",
            sa.column("check_type_code", sa.String),
            sa.column("description", sa.String),
        ),
        [
            {"check_type_code": "KYC", "description": "Know Your Customer"},
            {"check_type_code": "KYB", "description": "Know Your Business"},
            {"check_type_code": "SANCTIONS", "description": "Sanctions screening"},
            {"check_type_code": "CREDIT", "description": "Credit bureau check"},
            {"check_type_code": "REGISTRY", "description": "Business registry check"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "check_business_result",
            sa.column("check_business_result_code", sa.String),
            sa.column("description", sa.String),
        ),
        [
            {"check_business_result_code": "PASS", "description": "Automated pass"},
            {"check_business_result_code": "MANUAL_REVIEW", "description": "Requires manual review"},
            {"check_business_result_code": "FAIL", "description": "Automated fail"},
        ],
    )

    op.bulk_insert(
        sa.table(
            "decision_outcome",
            sa.column("decision_outcome_code", sa.String),
            sa.column("description", sa.String),
        ),
        [
            {"decision_outcome_code": "APPROVED", "description": "Approved"},
            {"decision_outcome_code": "MANUAL_REVIEW", "description": "Manual review"},
            {"decision_outcome_code": "REJECTED", "description": "Rejected"},
        ],
    )


def _seed_onboarding_flows() -> None:
    for country in ("SE", "ES", "PL"):
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_flow (country_code, party_type_code, flow_name, flow_version, is_active)
                VALUES (:country, 'PRIVATE', :flow_name, 1, true)
                """
            ).bindparams(country=country, flow_name=f"{country} PRIVATE Onboarding")
        )
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_flow (country_code, party_type_code, flow_name, flow_version, is_active)
                VALUES (:country, 'BUSINESS', :flow_name, 1, true)
                """
            ).bindparams(country=country, flow_name=f"{country} BUSINESS Onboarding")
        )

        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order)
                SELECT flow_id, 'COLLECT_PRIVATE_PROFILE', 'Collect applicant profile', 1
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'PRIVATE' AND flow_version = 1
                """
            ).bindparams(country=country)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order, check_type_code)
                SELECT flow_id, 'RUN_KYC', 'Run KYC check', 2, 'KYC'
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'PRIVATE' AND flow_version = 1
                """
            ).bindparams(country=country)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order, check_type_code)
                SELECT flow_id, 'RUN_SANCTIONS', 'Run sanctions screening', 3, 'SANCTIONS'
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'PRIVATE' AND flow_version = 1
                """
            ).bindparams(country=country)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order)
                SELECT flow_id, 'DECISION', 'Apply decision rules', 4
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'PRIVATE' AND flow_version = 1
                """
            ).bindparams(country=country)
        )

        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order)
                SELECT flow_id, 'COLLECT_BUSINESS_PROFILE', 'Collect business profile', 1
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'BUSINESS' AND flow_version = 1
                """
            ).bindparams(country=country)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order, check_type_code)
                SELECT flow_id, 'RUN_KYB', 'Run KYB check', 2, 'KYB'
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'BUSINESS' AND flow_version = 1
                """
            ).bindparams(country=country)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order, check_type_code)
                SELECT flow_id, 'RUN_REGISTRY', 'Run business registry check', 3, 'REGISTRY'
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'BUSINESS' AND flow_version = 1
                """
            ).bindparams(country=country)
        )
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order)
                SELECT flow_id, 'DECISION', 'Apply decision rules', 4
                FROM onboarding_flow
                WHERE country_code = :country AND party_type_code = 'BUSINESS' AND flow_version = 1
                """
            ).bindparams(country=country)
        )


def downgrade() -> None:
    op.drop_table("audit_event")
    op.drop_table("manual_review_case")
    op.drop_table("check_run")
    op.drop_table("application")
    op.drop_table("onboarding_step")
    op.drop_table("onboarding_flow")
    op.drop_table("decision_outcome")
    op.drop_table("check_business_result")
    op.drop_table("check_type")
    op.drop_table("step_status")
    op.drop_table("application_status")
    op.drop_table("party_type")
    op.drop_table("country")
    op.drop_table("users")
