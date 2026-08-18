
"""add SLA management

Revision ID: 3606cc025cf2
Revises: 99b5182b3f73
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3606cc025cf2"
down_revision: Union[str, Sequence[str], None] = "99b5182b3f73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================
    # CREATE SLA POLICIES TABLE
    # ========================================================

    op.create_table(
        "sla_policies",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "first_response_minutes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "resolution_minutes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("priority"),
    )

    op.create_index(
        "ix_sla_policies_id",
        "sla_policies",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_sla_policies_priority",
        "sla_policies",
        ["priority"],
        unique=True,
    )

    # ========================================================
    # ADD SLA COLUMNS TO TICKETS
    # ========================================================

    op.add_column(
        "tickets",
        sa.Column(
            "first_response_deadline",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tickets",
        sa.Column(
            "resolution_deadline",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tickets",
        sa.Column(
            "first_response_time",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tickets",
        sa.Column(
            "resolution_time",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # ========================================================
    # SLA STATUS
    #
    # Existing tickets already exist in the database.
    # Therefore we temporarily allow NULL, populate existing
    # tickets, and then make the column NOT NULL.
    # ========================================================

    op.add_column(
        "tickets",
        sa.Column(
            "sla_status",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.execute(
        "UPDATE tickets "
        "SET sla_status = 'within_sla' "
        "WHERE sla_status IS NULL"
    )

    op.alter_column(
        "tickets",
        "sla_status",
        existing_type=sa.String(length=20),
        nullable=False,
    )

    # ========================================================
    # SLA INDEXES
    # ========================================================

    op.create_index(
        "ix_tickets_first_response_deadline",
        "tickets",
        ["first_response_deadline"],
        unique=False,
    )

    op.create_index(
        "ix_tickets_resolution_deadline",
        "tickets",
        ["resolution_deadline"],
        unique=False,
    )

    op.create_index(
        "ix_tickets_sla_status",
        "tickets",
        ["sla_status"],
        unique=False,
    )


def downgrade() -> None:
    # ========================================================
    # REMOVE SLA INDEXES
    # ========================================================

    op.drop_index(
        "ix_tickets_sla_status",
        table_name="tickets",
    )

    op.drop_index(
        "ix_tickets_resolution_deadline",
        table_name="tickets",
    )

    op.drop_index(
        "ix_tickets_first_response_deadline",
        table_name="tickets",
    )

    # ========================================================
    # REMOVE SLA COLUMNS
    # ========================================================

    op.drop_column(
        "tickets",
        "sla_status",
    )

    op.drop_column(
        "tickets",
        "resolution_time",
    )

    op.drop_column(
        "tickets",
        "first_response_time",
    )

    op.drop_column(
        "tickets",
        "resolution_deadline",
    )

    op.drop_column(
        "tickets",
        "first_response_deadline",
    )

    # ========================================================
    # REMOVE SLA POLICY TABLE
    # ========================================================

    op.drop_index(
        "ix_sla_policies_priority",
        table_name="sla_policies",
    )

    op.drop_index(
        "ix_sla_policies_id",
        table_name="sla_policies",
    )

    op.drop_table(
        "sla_policies",
    )