import sys

sys.path.insert(0, "/Users/divyanshgolyan/Documents/GitHub/interaced-slackbots")
import os

print("Current working directory:", os.getcwd())
import asyncio
from app import create_app, db

# from sqlalchemy.ext.asyncio import AsyncEngine
# from app.database.models import Conversation, Message, File


# async def create_tables(engine: AsyncEngine):
#     async with engine.begin() as conn:
#         await conn.run_sync(db.metadata.create_all)


async def main():
    flask_app, _ = await create_app()

    # Assuming `create_app` returns the async engine as well
    # async_engine = flask_app.extensions["sqlalchemy"].db.engine

    # # Create tables if needed
    # await create_tables(async_engine)

    # Run the Flask application
    flask_app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    asyncio.run(main())
