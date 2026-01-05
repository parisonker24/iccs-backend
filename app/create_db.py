import asyncio
import asyncpg

async def create_database():
    # Connect to the default 'postgres' database to create the new database
    conn = await asyncpg.connect(
        user='postgres',
        password='postgres123',
        host='localhost',
        port=5432,
        database='postgres'
    )

    # Create the 'iccs' database if it doesn't exist
    await conn.execute('CREATE DATABASE iccs OWNER postgres;')

    await conn.close()
    print("Database 'iccs' created successfully.")

if __name__ == "__main__":
    asyncio.run(create_database())
