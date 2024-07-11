"""create product table

Revision ID: c957effbe191
Revises: add_order_and_order_item_tables
Create Date: 2024-07-12 00:58:43.659802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c957effbe191'
down_revision: Union[str, None] = 'add_order_and_order_item_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     op.create_table('product',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('last_modified_by', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    # Drop the customers table with CASCADE
    op.execute('DROP TABLE IF EXISTS product CASCADE')
