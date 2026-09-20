"""add app_setting

Revision ID: b7f3c2a91d40
Revises: 88c93884780f
Create Date: 2026-09-20 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f3c2a91d40'
down_revision = '88c93884780f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'app_setting',
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade():
    op.drop_table('app_setting')
