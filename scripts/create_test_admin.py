import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.db.session import async_session_maker
from app.crud import crud_user
from app.models.user import UserRole


async def main():
    email = "admin@example.com"
    username = "admin"
    password = "secret"

    async with async_session_maker() as session:
        # check if user exists
        existing = await crud_user.get_user_by_email(session, email)
        if existing:
            print(f"User with email {email} already exists (id={existing.id}). Updating role to admin and resetting password.")
            # update role
            existing.role = UserRole.admin
            # reset password
            from app.core.security import get_password_hash

            existing.hashed_password = get_password_hash(password)
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            print(f"Updated user {existing.email} -> role={existing.role}")
            return

        # create new user
        new_user = await crud_user.create_user(session, username=username, email=email, password=password)
        # set role to admin
        new_user.role = UserRole.admin
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        print("Created admin user:")
        print(f"  id: {new_user.id}")
        print(f"  email: {new_user.email}")
        print(f"  username: {new_user.username}")
        print("Use these credentials to obtain an access token via POST /auth/login")


if __name__ == "__main__":
    asyncio.run(main())
