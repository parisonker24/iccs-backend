import asyncio
import os
from app.services.embedding_service import EmbeddingService

async def _test_embedding_service():
    # Test 1: Initialization without API key
    print("Test 1: Initialization without API key")
    try:
        service = EmbeddingService()
        print("ERROR: Should have raised ValueError")
    except ValueError as e:
        print(f"SUCCESS: {e}")

    # Test 2: Initialization with API key (assuming it's set)
    print("\nTest 2: Initialization with API key")
    if not os.getenv("OPENAI_API_KEY"):
        print("SKIP: OPENAI_API_KEY not set")
    else:
        try:
            service = EmbeddingService()
            print("SUCCESS: Service initialized")
        except Exception as e:
            print(f"ERROR: {e}")

    # Test 3: Get embedding (if API key is set)
    print("\nTest 3: Get embedding")
    if not os.getenv("OPENAI_API_KEY"):
        print("SKIP: OPENAI_API_KEY not set")
    else:
        try:
            service = EmbeddingService()
            embedding = await service.get_embedding("Hello world")
            print(f"SUCCESS: Embedding length: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")
        except Exception as e:
            print(f"ERROR: {e}")


def test_embedding_service():
    asyncio.run(_test_embedding_service())


if __name__ == "__main__":
    asyncio.run(_test_embedding_service())
