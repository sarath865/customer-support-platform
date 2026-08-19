"""add audit logs

Revision ID: 24fd33851c24
Revises: 3606cc025cf2
Create Date: 2026-08-19 09:38:43.833494

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "24fd33851c24"
down_revision: Union[str, Sequence[str], None] = "3606cc025cf2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "ticket_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "old_value",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "new_value",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_audit_logs_action"),
        "audit_logs",
        ["action"],
        unique=False,
    )

    op.create_index(
        op.f("ix_audit_logs_id"),
        "audit_logs",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_audit_logs_ticket_id"),
        "audit_logs",
        ["ticket_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_audit_logs_user_id"),
        "audit_logs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_audit_logs_user_id"),
        table_name="audit_logs",
    )

    op.drop_index(
        op.f("ix_audit_logs_ticket_id"),
        table_name="audit_logs",
    )

    op.drop_index(
        op.f("ix_audit_logs_id"),
        table_name="audit_logs",
    )

    op.drop_index(
        op.f("ix_audit_logs_action"),
        table_name="audit_logs",
    )

    op.drop_table("audit_logs")
