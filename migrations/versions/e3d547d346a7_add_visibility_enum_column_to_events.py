"""Add visibility enum column to events

Revision ID: e3d547d346a7
Revises: 
Create Date: 2025-11-11 12:29:45.785020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3d547d346a7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Define the enum type
    event_visibility = sa.Enum('public', 'private', name='eventvisibility')
    event_visibility.create(op.get_bind())

    with op.batch_alter_table('events', schema=None) as batch_op:
        # Add column with server_default first
        batch_op.add_column(sa.Column('visibility', event_visibility, nullable=False, server_default='public'))



def downgrade():
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('visibility')

    sa.Enum(name='eventvisibility').drop(op.get_bind())

