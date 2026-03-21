"""add payment tickets

Revision ID: 20260320_0003
Revises: 20260320_0002
Create Date: 2026-03-20 20:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260320_0003"
down_revision = "20260320_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("customer_contact", sa.String(length=255), nullable=False),
        sa.Column("payment_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_card_number", sa.String(length=64), nullable=False),
        sa.Column("payment_card_holder", sa.String(length=255), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("screenshot_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("admin_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index(op.f("ix_payment_tickets_order_id"), "payment_tickets", ["order_id"], unique=True)
    op.create_index(op.f("ix_payment_tickets_user_id"), "payment_tickets", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_tickets_user_id"), table_name="payment_tickets")
    op.drop_index(op.f("ix_payment_tickets_order_id"), table_name="payment_tickets")
    op.drop_table("payment_tickets")
