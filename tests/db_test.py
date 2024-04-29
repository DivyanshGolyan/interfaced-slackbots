import sys

sys.path.append("/Users/divyanshgolyan/Documents/GitHub/interaced-slackbots")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.models import db
from app.config import *


async def create_tables():
    engine = create_async_engine(
        f"mysql+asyncmy://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}",
        echo=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(db.metadata.create_all)


import asyncio

asyncio.run(create_tables())
