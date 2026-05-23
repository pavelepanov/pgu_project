"""Add registration_complete field to users.

Revision ID: 0005_registration_complete
Revises: 0004_user_profile_expansion
Create Date: 2026-05-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005_registration_complete'
down_revision = '0004_user_profile_expansion'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('registration_complete', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'registration_complete')
