import sys
import os
import asyncio
from sqlalchemy import text

# Add current directory to sys.path
sys.path.append(os.getcwd())

from app.db.session import async_session_maker

async def test_db():
    print("Testing DB connection...")
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            print(f"DB Connection Success: {result.scalar()}")
    except Exception as e:
        print(f"DB Connection Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())
