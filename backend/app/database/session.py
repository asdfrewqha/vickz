from typing import AsyncGenerator

from app.database.adapter import adapter
from sqlalchemy.ext.asyncio import AsyncSession


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with adapter.SessionLocal() as session:
        yield session
