import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.models.product import Product
from app.services.embedding_service import EmbeddingService
from app.db.session import get_db
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 100

async def backfill_product_embeddings():
    """
    Background job to compute and save embeddings for products that don't have them.
    Processes products in chunks of 100 and logs progress.
    """
    logger.info("Starting product embedding backfill job")

    # Get database session
    db = next(get_db())

    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()
        logger.info("Embedding service initialized")

        total_processed = 0
        chunk_count = 0

        while True:
            chunk_count += 1

            # Query products without embeddings, limit to chunk size
            query = select(Product).where(Product.product_embedding.is_(None)).limit(CHUNK_SIZE)
            result = await db.execute(query)
            products = result.scalars().all()

            if not products:
                logger.info(f"No more products to process. Total processed: {total_processed}")
                break

            logger.info(f"Processing chunk {chunk_count} with {len(products)} products")

            # Process each product in the chunk
            for product in products:
                try:
                    # Generate text for embedding
                    text = f"{product.name or ''} {product.description or ''}".strip()
                    if text:
                        embedding = await embedding_service.get_embedding(text)
                        product.product_embedding = embedding
                        total_processed += 1
                    else:
                        logger.warning(f"Product {product.id} has no text to embed")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for product {product.id}: {e}")

            # Commit the chunk
            await db.commit()
            logger.info(f"Chunk {chunk_count} processed. Total processed so far: {total_processed}")

        logger.info(f"Product embedding backfill completed. Total products processed: {total_processed}")

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(backfill_product_embeddings())
