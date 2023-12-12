"""empty message

Revision ID: 1ea00b755ea8
Revises: ffd267ccf7eb
Create Date: 2023-12-11 10:30:04.028187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ea00b755ea8'
down_revision = 'ffd267ccf7eb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.add_column(sa.Column('campaign_type', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.drop_column('campaign_type')

    # ### end Alembic commands ###
