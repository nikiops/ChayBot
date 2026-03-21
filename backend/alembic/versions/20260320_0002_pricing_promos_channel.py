"""add pack sizes, promos, and channel sync

Revision ID: 20260320_0002
Revises: 20260320_0001
Create Date: 2026-03-20 14:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260320_0002"
down_revision = "20260320_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    op.create_table(
        "product_pack_sizes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("weight_grams", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("old_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("stock_qty", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_pack_sizes_product_id"), "product_pack_sizes", ["product_id"], unique=False)

    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("badge_text", sa.String(length=50), nullable=True),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_sitewide", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_promotions_slug"), "promotions", ["slug"], unique=True)

    op.create_table(
        "promotion_products",
        sa.Column("promotion_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("promotion_id", "product_id"),
    )

    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_sitewide", sa.Boolean(), nullable=False),
        sa.Column("minimum_order_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("times_used", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_promo_codes_code"), "promo_codes", ["code"], unique=True)

    op.create_table(
        "promo_code_products",
        sa.Column("promo_code_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("promo_code_id", "product_id"),
    )

    op.create_table(
        "channel_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("channel_chat_id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("deep_link", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_channel_posts_source_id"), "channel_posts", ["source_id"], unique=False)
    op.create_index(op.f("ix_channel_posts_source_type"), "channel_posts", ["source_type"], unique=False)

    with op.batch_alter_table("cart_items", recreate="always") as batch:
        batch.add_column(sa.Column("pack_size_id", sa.Integer(), nullable=True))
        batch.create_index(op.f("ix_cart_items_pack_size_id"), ["pack_size_id"], unique=False)
        batch.drop_constraint("uq_cart_items_user_product", type_="unique")
        batch.create_foreign_key(
            "fk_cart_items_pack_size_id_product_pack_sizes",
            "product_pack_sizes",
            ["pack_size_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_unique_constraint(
            "uq_cart_items_user_product_pack",
            ["user_id", "product_id", "pack_size_id"],
        )

    if dialect == "sqlite":
        with op.batch_alter_table("orders", recreate="always") as batch:
            batch.add_column(
                sa.Column("subtotal_amount", sa.Numeric(10, 2), server_default=sa.text("0"), nullable=False)
            )
            batch.add_column(
                sa.Column("discount_amount", sa.Numeric(10, 2), server_default=sa.text("0"), nullable=False)
            )
            batch.add_column(sa.Column("promo_code", sa.String(length=50), nullable=True))

        with op.batch_alter_table("order_items", recreate="always") as batch:
            batch.add_column(sa.Column("pack_size_id", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("pack_label", sa.String(length=50), nullable=True))
            batch.add_column(sa.Column("pack_weight_grams", sa.Integer(), nullable=True))
            batch.create_index(op.f("ix_order_items_pack_size_id"), ["pack_size_id"], unique=False)
            batch.create_foreign_key(
                "fk_order_items_pack_size_id_product_pack_sizes",
                "product_pack_sizes",
                ["pack_size_id"],
                ["id"],
                ondelete="SET NULL",
            )
    else:
        op.add_column(
            "orders",
            sa.Column("subtotal_amount", sa.Numeric(10, 2), server_default=sa.text("0"), nullable=False),
        )
        op.add_column(
            "orders",
            sa.Column("discount_amount", sa.Numeric(10, 2), server_default=sa.text("0"), nullable=False),
        )
        op.add_column("orders", sa.Column("promo_code", sa.String(length=50), nullable=True))

        op.add_column("order_items", sa.Column("pack_size_id", sa.Integer(), nullable=True))
        op.add_column("order_items", sa.Column("pack_label", sa.String(length=50), nullable=True))
        op.add_column("order_items", sa.Column("pack_weight_grams", sa.Integer(), nullable=True))
        op.create_index(op.f("ix_order_items_pack_size_id"), "order_items", ["pack_size_id"], unique=False)
        op.create_foreign_key(
            "fk_order_items_pack_size_id_product_pack_sizes",
            "order_items",
            "product_pack_sizes",
            ["pack_size_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":
        with op.batch_alter_table("order_items", recreate="always") as batch:
            batch.drop_constraint("fk_order_items_pack_size_id_product_pack_sizes", type_="foreignkey")
            batch.drop_index(op.f("ix_order_items_pack_size_id"))
            batch.drop_column("pack_weight_grams")
            batch.drop_column("pack_label")
            batch.drop_column("pack_size_id")

        with op.batch_alter_table("orders", recreate="always") as batch:
            batch.drop_column("promo_code")
            batch.drop_column("discount_amount")
            batch.drop_column("subtotal_amount")
    else:
        op.drop_constraint("fk_order_items_pack_size_id_product_pack_sizes", "order_items", type_="foreignkey")
        op.drop_index(op.f("ix_order_items_pack_size_id"), table_name="order_items")
        op.drop_column("order_items", "pack_weight_grams")
        op.drop_column("order_items", "pack_label")
        op.drop_column("order_items", "pack_size_id")

        op.drop_column("orders", "promo_code")
        op.drop_column("orders", "discount_amount")
        op.drop_column("orders", "subtotal_amount")

    with op.batch_alter_table("cart_items", recreate="always") as batch:
        batch.drop_constraint("uq_cart_items_user_product_pack", type_="unique")
        batch.drop_constraint("fk_cart_items_pack_size_id_product_pack_sizes", type_="foreignkey")
        batch.create_unique_constraint("uq_cart_items_user_product", ["user_id", "product_id"])
        batch.drop_index(op.f("ix_cart_items_pack_size_id"))
        batch.drop_column("pack_size_id")

    op.drop_index(op.f("ix_channel_posts_source_type"), table_name="channel_posts")
    op.drop_index(op.f("ix_channel_posts_source_id"), table_name="channel_posts")
    op.drop_table("channel_posts")

    op.drop_table("promo_code_products")
    op.drop_index(op.f("ix_promo_codes_code"), table_name="promo_codes")
    op.drop_table("promo_codes")

    op.drop_table("promotion_products")
    op.drop_index(op.f("ix_promotions_slug"), table_name="promotions")
    op.drop_table("promotions")

    op.drop_index(op.f("ix_product_pack_sizes_product_id"), table_name="product_pack_sizes")
    op.drop_table("product_pack_sizes")
