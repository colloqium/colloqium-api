"""empty message

Revision ID: d20323883224
Revises: f58af8956a45
Create Date: 2023-12-25 17:30:38.615214

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd20323883224'
down_revision = 'f58af8956a45'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('alert',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=True),
    sa.Column('voter_id', sa.Integer(), nullable=True),
    sa.Column('alert_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('alert_message', sa.Text(), nullable=True),
    sa.Column('alert_status', sa.Enum('SENT', 'SEEN', 'PROCESSED', name='alertstatus'), nullable=True),
    sa.ForeignKeyConstraint(['sender_id'], ['sender.id'], ),
    sa.ForeignKeyConstraint(['voter_id'], ['voter.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('alert')
    # ### end Alembic commands ###