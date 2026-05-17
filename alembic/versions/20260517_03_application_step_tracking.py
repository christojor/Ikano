"""add application step tracking table

Revision ID: 20260517_03
Revises: 20260517_02
Create Date: 2026-05-17 20:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260517_03"
down_revision: str | None = "20260517_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_step",
        sa.Column("application_step_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("application.application_id"), nullable=False),
        sa.Column("step_code", sa.String(length=32), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column(
            "step_status_code",
            sa.String(length=24),
            sa.ForeignKey("step_status.step_status_code"),
            nullable=False,
        ),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("application_step")
