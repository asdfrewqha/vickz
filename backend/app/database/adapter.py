from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Literal, Type, TypeVar

from app.core.logging import get_logger
from app.core.settings import settings
from app.database.models import Base
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.sql import and_, or_
from thefuzz import fuzz, process

logger = get_logger()

T = TypeVar("T")


class AsyncDatabaseAdapter:
    def __init__(self, database_url: str = settings.db_settings.db_url) -> None:
        self.engine = create_async_engine(database_url, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_or_create_session(
        self, session: AsyncSession | None = None
    ) -> AsyncGenerator[AsyncSession, None]:
        if session:
            yield session
        else:
            async with self.SessionLocal() as new_session:
                yield new_session

    async def initialize_tables(self) -> None:
        logger.info(settings.db_settings.db_url)
        logger.info("Tables are created or exists")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_all(self, model, session: AsyncSession | None = None) -> List[Any]:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(select(model))
            return result.scalars().all()

    async def get_by_id(self, model, id, session: AsyncSession | None = None) -> Any:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(select(model).where(model.id == id))
            return result.scalar_one_or_none()

    async def get_by_value(
        self, model, parameter: str, parameter_value: Any, session: AsyncSession | None = None
    ) -> List[Any]:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(
                select(model).where(getattr(model, parameter) == parameter_value)
            )
            return result.scalars().all()

    async def get_by_values(
        self,
        model: Type[T],
        and_conditions: dict = None,
        or_conditions: dict = None,
        mode: Literal["and", "or", "mixed"] = "and",
        session: AsyncSession | None = None,
    ) -> List[T]:
        async with self.get_or_create_session(session) as s:
            query = select(model)

            and_conditions = and_conditions or {}
            or_conditions = or_conditions or {}

            def validate_keys(conditions):
                for key in conditions:
                    if not hasattr(model, key):
                        raise ValueError(f"Invalid field: {key}")

            validate_keys(and_conditions)
            validate_keys(or_conditions)

            and_clauses = [getattr(model, k) == v for k, v in and_conditions.items()]
            or_clauses = [getattr(model, k) == v for k, v in or_conditions.items()]

            if mode == "and":
                if and_clauses:
                    query = query.where(and_(*and_clauses))
            elif mode == "or":
                if or_clauses:
                    query = query.where(or_(*or_clauses))
            elif mode == "mixed":
                combined = []
                if and_clauses:
                    combined.append(and_(*and_clauses))
                if or_clauses:
                    combined.append(or_(*or_clauses))
                if combined:
                    query = query.where(and_(*combined))

            result = await s.execute(query)
            return result.scalars().all()

    async def insert(self, model, insert_dict: dict, session: AsyncSession | None = None) -> Any:
        async with self.get_or_create_session(session) as s:
            record = model(**insert_dict)
            s.add(record)
            await s.commit()
            await s.refresh(record)
            return record

    async def update_by_id(
        self, model, record_id: int, updates: dict, session: AsyncSession | None = None
    ):
        async with self.get_or_create_session(session) as s:
            stmt = update(model).where(model.id == record_id).values(**updates)
            await s.execute(stmt)
            await s.commit()

    async def update_by_value(
        self, model, filters: dict, updates: dict, session: AsyncSession | None = None
    ):
        async with self.get_or_create_session(session) as s:
            conditions = [getattr(model, key) == value for key, value in filters.items()]
            stmt = update(model).where(and_(*conditions)).values(**updates)
            await s.execute(stmt)
            await s.commit()

    async def delete(self, model, id: int, session: AsyncSession | None = None) -> Any:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(select(model).where(model.id == id))
            record = result.scalar_one_or_none()
            if record:
                await s.delete(record)
                await s.commit()
            return record

    async def delete_by_value(
        self, model, parameter: str, parameter_value: Any, session: AsyncSession | None = None
    ) -> List[Any]:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(
                select(model).where(getattr(model, parameter) == parameter_value)
            )
            records = result.scalars().all()
            for record in records:
                await s.delete(record)
            await s.commit()
            return records

    async def get_comment_replies(self, comment_id: Any, session: AsyncSession | None = None):
        from app.database.models import Comment

        async with self.get_or_create_session(session) as s:
            stmt = select(Comment).where(Comment.parent_id == comment_id)
            result = await s.execute(stmt)
            return result.scalars().all()

    async def get_all_with_join(
        self,
        parent_model,
        child_model,
        parent_column_name: str,
        isouter: bool = True,
        session: AsyncSession | None = None,
    ) -> List[Any]:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(
                select(parent_model, child_model).join(
                    child_model,
                    getattr(parent_model, parent_column_name)
                    == getattr(child_model, parent_column_name),
                    isouter=isouter,
                )
            )
            return result.all()

    async def get_by_id_with_join(
        self,
        parent_model,
        child_model,
        parent_id: int,
        parent_column_name: str,
        isouter: bool = True,
        session: AsyncSession | None = None,
    ) -> Any:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(
                select(parent_model, child_model)
                .join(
                    child_model,
                    getattr(parent_model, parent_column_name)
                    == getattr(child_model, parent_column_name),
                    isouter=isouter,
                )
                .where(getattr(parent_model, "id") == parent_id)
            )
            return result.scalar_one_or_none()

    async def get_by_value_with_join(
        self,
        parent_model,
        child_model,
        parameter: str,
        parameter_value: Any,
        parent_column_name: str,
        isouter: bool = True,
        session: AsyncSession | None = None,
    ) -> List[Any]:
        async with self.get_or_create_session(session) as s:
            result = await s.execute(
                select(parent_model, child_model)
                .join(
                    child_model,
                    getattr(parent_model, parent_column_name)
                    == getattr(child_model, parent_column_name),
                    isouter=isouter,
                )
                .where(getattr(parent_model, parameter) == parameter_value)
            )
            return result.all()

    async def get_by_cond(self, model, *conditions, session: AsyncSession | None = None):
        async with self.get_or_create_session(session) as s:
            query = select(model)
            for i in range(0, len(conditions), 3):
                column = getattr(model, conditions[i])
                value = conditions[i + 1]
                op = conditions[i + 2]
                if op == ">":
                    query = query.where(column > value)
                elif op == "<":
                    query = query.where(column < value)
                elif op == ">=":
                    query = query.where(column >= value)
                elif op == "<=":
                    query = query.where(column <= value)
                elif op == "==":
                    query = query.where(column == value)
                elif op == "!=":
                    query = query.where(column != value)
                else:
                    raise ValueError(f"Unsupported operator: {op}")
            result = await s.execute(query)
            return result.scalars().all()

    async def get_count(
        self, model, conditions: dict = None, session: AsyncSession | None = None
    ) -> int:
        async with self.get_or_create_session(session) as s:
            query = select(func.count()).select_from(model)
            if conditions:
                for key, value in conditions.items():
                    query = query.where(getattr(model, key) == value)
            result = await s.execute(query)
            return result.scalar()

    async def get_count_cond(self, model, *conditions, session: AsyncSession | None = None) -> int:
        async with self.get_or_create_session(session) as s:
            query = select(func.count()).select_from(model)
            for i in range(0, len(conditions), 3):
                column = getattr(model, conditions[i])
                value = conditions[i + 1]
                op = conditions[i + 2]
                if op == ">":
                    query = query.where(column > value)
                elif op == "<":
                    query = query.where(column < value)
                elif op == ">=":
                    query = query.where(column >= value)
                elif op == "<=":
                    query = query.where(column <= value)
                elif op == "==":
                    query = query.where(column == value)
                elif op == "!=":
                    query = query.where(column != value)
                else:
                    raise ValueError(f"Unsupported operator: {op}")
            result = await s.execute(query)
            return result.scalar()

    async def find_similar_value(
        self,
        model,
        column_name: str,
        search_value: str,
        limit: int = 5,
        similarity_threshold: int = 85,
        session: AsyncSession | None = None,
    ) -> list:
        all_records = await self.get_all(model, session=session)
        values = []
        records_map = {}
        for record in all_records:
            value = getattr(record, column_name)
            if value not in records_map:
                records_map[value] = []
            records_map[value].append(record)
            values.append(value)
        results = process.extractBests(
            search_value,
            list(set(values)),
            limit=limit * 5,
            score_cutoff=similarity_threshold,
            scorer=fuzz.token_sort_ratio,
        )
        output = []
        for value, score in results:
            for record in records_map[value]:
                record_dict = {}
                for column in record.__table__.columns:
                    record_dict[column.name] = getattr(record, column.name)
                record_dict["similarity"] = score
                output.append(record_dict)
        output.sort(key=lambda x: x["similarity"], reverse=True)
        return output[:limit]


adapter = AsyncDatabaseAdapter()
