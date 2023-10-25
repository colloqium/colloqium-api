"""empty message

Revision ID: a66dbcef884a
Revises: abf7031a7411
Create Date: 2023-09-29 17:16:45.734661

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a66dbcef884a'
down_revision = 'abf7031a7411'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('agent',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('sender_voter_relationship_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['sender_voter_relationship_id'], ['sender_voter_relationship.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('agent')
    # ### end Alembic commands ###