"""Initial migration

Revision ID: 036cb5a658a5
Revises: 
Create Date: 2024-08-30 14:29:19.464746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '036cb5a658a5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('surname', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('phone', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hash_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('delete_at', sa.DateTime, nullable=True),
        sa.Column('last_active', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_staff', sa.Boolean, default=False, nullable=False),
        sa.Column('is_superuser', sa.Boolean, default=False, nullable=False),
        sa.Column('role', sa.String(length=255), default='new-user', nullable=False),
        sa.Column('permissions', sa.String(length=255), default="[]", nullable=False),
        sa.Column('avatar', sa.String(length=255), default='https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png', nullable=False),
        sa.Column('status', sa.String(length=999), default='new-user', nullable=False),
        sa.Column('token', sa.String(length=255), default='', nullable=False),
        sa.Column('refresh_token', sa.String(length=255), default='', nullable=False),
    )
    
    op.create_table(
        'users_token',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(length=255), unique=True, nullable=False),
        sa.Column('expiration', sa.DateTime, nullable=False),
    )

def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('users_token')
