"""add_product_embedding_vector_column

Revision ID: 4682b39fb399
Revises: 1de625ffc30d
Create Date: 2025-12-04 16:53:31.204892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '4682b39fb399'
down_revision: Union[str, Sequence[str], None] = '1de625ffc30d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The original migration added the `vector` extension and a `vector`-typed
    # column. Some PostgreSQL installations (notably local Windows or
    # non-pgvector builds) do not have the pgvector extension available.
    # To allow migrations to run in such environments we avoid creating the
    # extension here and store embeddings as TEXT (JSON-encoded) instead.
    # If you later install pgvector on the server, you can convert this
    # column to the native `vector` type and adjust code accordingly.

    # NOTE: deliberately NOT executing `CREATE EXTENSION IF NOT EXISTS vector`
    # op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add product_embedding column to products table as TEXT to avoid
    # requiring the pgvector extension at migration time. Use a raw SQL
    # `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` so the migration is
    # idempotent in case the column already exists.
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS product_embedding TEXT")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the product_embedding column
    op.drop_column('products', 'product_embedding')
    # Optionally drop the extension if no longer needed
    # op.execute("DROP EXTENSION IF EXISTS vector")
