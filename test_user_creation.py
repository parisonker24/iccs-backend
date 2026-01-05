import asyncio
from app.db.session import async_session_maker
from app.crud import crud_user

async def _test_user_creation():
    async with async_session_maker() as session:
        try:
            user = await crud_user.create_user(session, "testuser", "test@example.com", "testpass123")
            print(f"User created: {user}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def test_user_creation():
    asyncio.run(_test_user_creation())


if __name__ == "__main__":
    asyncio.run(_test_user_creation())
