"""first

Revision ID: 0991841df087
Revises: 
Create Date: 2020-07-17 03:35:30.662343

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0991841df087'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('applications_states',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('applications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cadnum', sa.String(length=100), nullable=True),
    sa.Column('foreign_id', sa.String(length=20), nullable=True),
    sa.Column('foreign_status', sa.String(length=100), nullable=True),
    sa.Column('foreign_created', sa.DateTime(), nullable=True),
    sa.Column('result', sa.String(), nullable=True),
    sa.Column('inserted', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('state_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['state_id'], ['applications_states.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('foreign_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('applications')
    op.drop_table('applications_states')
    # ### end Alembic commands ###