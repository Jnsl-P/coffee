"""empty message

Revision ID: 0a287a3e0c05
Revises: 6efa47ee5bca
Create Date: 2024-12-15 11:35:50.240156

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a287a3e0c05'
down_revision = '6efa47ee5bca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('batch_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_batch_session_user', 'user', ['id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('batch_session', schema=None) as batch_op:
        batch_op.drop_constraint('fk_batch_session_user', type_='foreignkey')
        batch_op.drop_column('id')

    # ### end Alembic commands ###
