"""empty message

Revision ID: fae6563d0018
Revises: c4caab3fd940
Create Date: 2023-08-10 14:15:44.431928

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fae6563d0018'
down_revision = 'c4caab3fd940'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.add_column(sa.Column('policy_insights', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.drop_column('policy_insights')

    # ### end Alembic commands ###
