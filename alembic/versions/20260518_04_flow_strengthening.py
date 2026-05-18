"""add address and bank checks and strengthen active flows

Revision ID: 20260518_04
Revises: 20260517_03
Create Date: 2026-05-18 11:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260518_04"
down_revision: str | None = "20260517_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO check_type (check_type_code, description)
            VALUES
                ('ADDRESS', 'Address verification check'),
                ('BANK', 'Bank account ownership check')
            ON CONFLICT (check_type_code) DO NOTHING
            """
        )
    )

    _deactivate_existing_active_flows()
    _seed_private_v3_flows()
    _seed_business_v2_flows()


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM onboarding_step
            WHERE flow_id IN (
                SELECT flow_id
                FROM onboarding_flow
                WHERE (party_type_code = 'PRIVATE' AND flow_version = 3)
                   OR (party_type_code = 'BUSINESS' AND flow_version = 2)
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            DELETE FROM onboarding_flow
            WHERE (party_type_code = 'PRIVATE' AND flow_version = 3)
               OR (party_type_code = 'BUSINESS' AND flow_version = 2)
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE onboarding_flow
            SET is_active = CASE
                WHEN (party_type_code = 'PRIVATE' AND flow_version = 2)
                  OR (party_type_code = 'BUSINESS' AND flow_version = 1)
                THEN true
                ELSE false
            END
            WHERE party_type_code IN ('PRIVATE', 'BUSINESS')
            """
        )
    )


def _deactivate_existing_active_flows() -> None:
    op.execute(
        sa.text(
            """
            UPDATE onboarding_flow
            SET is_active = false
            WHERE party_type_code IN ('PRIVATE', 'BUSINESS')
              AND is_active = true
            """
        )
    )


def _seed_private_v3_flows() -> None:
    for country in ("SE", "ES", "PL"):
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_flow (country_code, party_type_code, flow_name, flow_version, is_active)
                VALUES (:country, 'PRIVATE', :flow_name, 3, true)
                """
            ).bindparams(country=country, flow_name=f"{country} PRIVATE Onboarding v3")
        )

        if country == "SE":
            steps = [
                ("COLLECT_SE_IDENTITY", "Collect personal identity number", 1, None),
                ("RUN_SE_BANKID", "Run BankID-style identity verification", 2, "KYC"),
                ("CONFIRM_SE_CONTACT", "Confirm contact details and address", 3, "ADDRESS"),
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
                ("RUN_SE_CREDIT", "Run credit bureau and affordability decision", 6, "CREDIT"),
                ("REVIEW_SE_SUBMIT", "Review summary, accept terms, and submit", 7, None),
            ]
        elif country == "ES":
            steps = [
                ("COLLECT_ES_DNI_NIE", "Collect DNI/NIE", 1, None),
                ("RUN_ES_IDENTITY", "Run Clave/DNIe document verification", 2, "KYC"),
                (
                    "CONFIRM_ES_CONTACT",
                    "Confirm contact details, province, and address",
                    3,
                    "ADDRESS",
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
                ("RUN_ES_CREDIT", "Run credit bureau and affordability decision", 6, "CREDIT"),
                ("REVIEW_ES_SUBMIT", "Review summary, accept terms, and submit", 7, None),
            ]
        else:
            steps = [
                ("COLLECT_PL_PESEL", "Collect PESEL", 1, None),
                ("RUN_PL_EID", "Run eID-style identity verification", 2, "KYC"),
                (
                    "CONFIRM_PL_CONTACT",
                    "Confirm contact details and registered address",
                    3,
                    "ADDRESS",
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
                ("RUN_PL_BIK", "Run BIK-style credit bureau and affordability decision", 6, "CREDIT"),
                ("REVIEW_PL_SUBMIT", "Review summary, accept terms, and submit", 7, None),
            ]

        _insert_steps(country=country, party_type="PRIVATE", version=3, steps=steps)


def _seed_business_v2_flows() -> None:
    for country in ("SE", "ES", "PL"):
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_flow (country_code, party_type_code, flow_name, flow_version, is_active)
                VALUES (:country, 'BUSINESS', :flow_name, 2, true)
                """
            ).bindparams(country=country, flow_name=f"{country} BUSINESS Onboarding v2")
        )

        if country == "SE":
            step_2_title = "Run Swedish KYB and legal entity verification"
            step_3_title = "Run Bolagsverket-style registry check"
            step_7_title = "Review authorized signatory and verify payout account"
        elif country == "ES":
            step_2_title = "Run Spanish KYB and legal entity verification"
            step_3_title = "Run Registro Mercantil registry check"
            step_7_title = "Review authorized signatory and verify settlement account"
        else:
            step_2_title = "Run Polish KYB and legal entity verification"
            step_3_title = "Run KRS/CEIDG registry check"
            step_7_title = "Review authorized signatory and verify account ownership"

        steps = [
            ("COLLECT_BUSINESS_PROFILE", "Collect business profile", 1, None),
            ("RUN_KYB", step_2_title, 2, "KYB"),
            ("RUN_REGISTRY", step_3_title, 3, "REGISTRY"),
            (
                "VERIFY_BUSINESS_REPRESENTATIVE",
                "Verify legal representative identity",
                4,
                "KYC",
            ),
            (
                "CAPTURE_BUSINESS_OWNERSHIP",
                "Capture beneficial ownership and sanctions context",
                5,
                "SANCTIONS",
            ),
            ("RUN_BUSINESS_CREDIT", "Run business credit and affordability check", 6, "CREDIT"),
            ("REVIEW_BUSINESS_SUBMIT", step_7_title, 7, "BANK"),
        ]

        _insert_steps(country=country, party_type="BUSINESS", version=2, steps=steps)


def _insert_steps(
    *,
    country: str,
    party_type: str,
    version: int,
    steps: list[tuple[str, str, int, str | None]],
) -> None:
    for step_code, step_title, step_order, check_type_code in steps:
        op.execute(
            sa.text(
                """
                INSERT INTO onboarding_step (flow_id, step_code, step_title, step_order, check_type_code)
                SELECT flow_id, :step_code, :step_title, :step_order, :check_type_code
                FROM onboarding_flow
                WHERE country_code = :country
                  AND party_type_code = :party_type
                  AND flow_version = :version
                """
            ).bindparams(
                country=country,
                party_type=party_type,
                version=version,
                step_code=step_code,
                step_title=step_title,
                step_order=step_order,
                check_type_code=check_type_code,
            )
        )
