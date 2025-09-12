"""Add email verification and last login fields to users

Revision ID: 002
Revises: 001
Create Date: 2025-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email_verified column to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True, default=False))
    
    # Add last_login column to users table
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    
    # Set default values for existing users
    op.execute("UPDATE users SET email_verified = false WHERE email_verified IS NULL")
    
    # Make email_verified not nullable after setting defaults
    op.alter_column('users', 'email_verified', nullable=False)


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'email_verified')