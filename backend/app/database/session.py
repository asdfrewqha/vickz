from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.adapter import adapter


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with adapter.SessionLocal() as session:
        yield session
