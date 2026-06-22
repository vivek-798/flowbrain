"""add_relevance_columns_to_emails

Revision ID: 281545bf7658
Revises: 3c868e58b45a
Create Date: 2026-06-22 12:35:22.057745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '281545bf7658'
down_revision: Union[str, Sequence[str], None] = '3c868e58b45a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('emails') as batch_op:
        batch_op.add_column(sa.Column('relevance_checked', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('is_relevant', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('relevance_category', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('relevance_reason', sa.String(), nullable=True))
        batch_op.alter_column('is_excluded',
                   existing_type=sa.BOOLEAN(),
                   nullable=False,
                   server_default=sa.text('0'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('emails') as batch_op:
        batch_op.alter_column('is_excluded',
                   existing_type=sa.BOOLEAN(),
                   nullable=True)
        batch_op.drop_column('relevance_reason')
        batch_op.drop_column('relevance_category')
        batch_op.drop_column('is_relevant')
        batch_op.drop_column('relevance_checked')
