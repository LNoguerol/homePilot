"""criar tabela usuarios

Revision ID: 0001
Revises:
Create Date: 2026-07-28

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=False),
        sa.Column("estado", sa.String(2), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)


def downgrade() -> None:
    op.drop_table("usuarios")
