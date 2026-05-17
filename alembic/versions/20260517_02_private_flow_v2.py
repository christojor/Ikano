"""seed v2 private onboarding flows

Revision ID: 20260517_02
Revises: 20260517_01
Create Date: 2026-05-17 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260517_02"
down_revision: str | None = "20260517_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for country in ("SE", "ES", "PL"):
        op.execute(
            sa.text(
                """
                UPDATE onboarding_flow
                SET is_active = false
                WHERE country_code = :country
                  AND party_type_code = 'PRIVATE'
                  AND flow_version = 1
                """
            ).bindparams(country=country)
        )

    _seed_private_flow_v2(
        country="SE",
        flow_name="SE PRIVATE Onboarding v2",
        steps=[
            ("COLLECT_SE_IDENTITY", "Collect personal identity number", 1, None),
            (
                "RUN_SE_BANKID",
                "Run BankID-style identity verification",
                2,
                "KYC",
            ),
            (
                "CONFIRM_SE_CONTACT",
                "Confirm contact details and address",
                3,
                None,
            ),
            (
                "CAPTURE_SE_CONSENT",
                "Capture consent, PEP/sanctions, and tax residency",
                4,
                "SANCTIONS",
            ),
            (
                "COLLECT_SE_AFFORD",
                "Collect employment, income, and affordability inputs",
                5,
                None,
            ),
            (
                "RUN_SE_CREDIT",
                "Run credit bureau and affordability decision",
                6,
                "CREDIT",
            ),
            (
                "REVIEW_SE_SUBMIT",
                "Review summary, accept terms, and submit",
                7,
                None,
            ),
        ],
    )

    _seed_private_flow_v2(
        country="ES",
        flow_name="ES PRIVATE Onboarding v2",
        steps=[
            ("COLLECT_ES_DNI_NIE", "Collect DNI/NIE", 1, None),
            (
                "RUN_ES_IDENTITY",
                "Run Clave/DNIe document verification",
                2,
                "KYC",
            ),
            (
                "CONFIRM_ES_CONTACT",
                "Confirm contact details, province, and address",
                3,
                None,
            ),
            (
                "CAPTURE_ES_CONSENT",
                "Capture consent and PEP/sanctions declaration",
                4,
                "SANCTIONS",
            ),
            (
                "COLLECT_ES_AFFORD",
                "Collect employment, income, housing costs, and dependants",
                5,
                None,
            ),
            (
                "RUN_ES_CREDIT",
                "Run credit bureau and affordability decision",
                6,
                "CREDIT",
            ),
            (
                "REVIEW_ES_SUBMIT",
                "Review summary, accept terms, and submit",
                7,
                None,
            ),
        ],
    )

    _seed_private_flow_v2(
        country="PL",
        flow_name="PL PRIVATE Onboarding v2",
        steps=[
            ("COLLECT_PL_PESEL", "Collect PESEL", 1, None),
            (
                "RUN_PL_EID",
                "Run eID-style identity verification",
                2,
                "KYC",
            ),
            (
                "CONFIRM_PL_CONTACT",
                "Confirm contact details and registered address",
                3,
                None,
            ),
            (
                "CAPTURE_PL_CONSENT",
                "Capture consent and PEP/sanctions declaration",
                4,
                "SANCTIONS",
            ),
            (
                "COLLECT_PL_AFFORD",
                "Collect employment, income, and affordability inputs",
                5,
                None,
            ),
            (
                "RUN_PL_BIK",
                "Run BIK-style credit bureau and affordability decision",
                6,
                "CREDIT",
            ),
            (
                "REVIEW_PL_SUBMIT",
                "Review summary, accept terms, and submit",
                7,
                None,
            ),
        ],
    )


def _seed_private_flow_v2(
    *,
    country: str,
    flow_name: str,
    steps: list[tuple[str, str, int, str | None]],
) -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO onboarding_flow (country_code, party_type_code, flow_name, flow_version, is_active)
            VALUES (:country, 'PRIVATE', :flow_name, 2, true)
            """
        ).bindparams(country=country, flow_name=flow_name)
    )

    for step_code, step_title, step_order, check_type_code in steps:
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order, check_type_code)
                SELECT flow_id, :step_code, :step_title, :step_order, :check_type_code
                FROM onboarding_flow
                WHERE country_code = :country
                  AND party_type_code = 'PRIVATE'
                  AND flow_version = 2
                """
            ).bindparams(
                country=country,
                step_code=step_code,
                step_title=step_title,
                step_order=step_order,
                check_type_code=check_type_code,
            )
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM onboarding_step
            WHERE flow_id IN (
                SELECT flow_id
                FROM onboarding_flow
                WHERE party_type_code = 'PRIVATE' AND flow_version = 2
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            DELETE FROM onboarding_flow
            WHERE party_type_code = 'PRIVATE' AND flow_version = 2
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE onboarding_flow
            SET is_active = true
            WHERE party_type_code = 'PRIVATE' AND flow_version = 1
            """
        )
    )
