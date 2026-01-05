"""add userrole enum and role column

Revision ID: 0001_add_user_role
Revises: None
Create Date: 2025-11-27 17:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_user_role'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type if not exists and add role column with default
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
            CREATE TYPE userrole AS ENUM ('admin','vendor','customer','delivery_partner');
        END IF;
    END
    $$;
    """)

    # Add the column if it doesn't exist
    op.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role userrole DEFAULT 'customer' NOT NULL;
    """)


def downgrade() -> None:
    # Remove the role column if present
    op.execute("""
    ALTER TABLE users
    DROP COLUMN IF EXISTS role;
    """)

    # Drop enum if exists (be careful if other tables use it)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
            DROP TYPE userrole;
        END IF;
    END
    $$;
    """)
