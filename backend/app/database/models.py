from uuid import UUID
import inflect

from sqlalchemy import Boolean, Integer, String, Uuid, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, declared_attr, relationship
from sqlalchemy.sql import func

from app.database.mixins.id_mixins import IDMixin
from app.database.mixins.timestamp_mixins import TimestampsMixin
from app.core.settings import settings

p = inflect.engine()


class Base:
    @declared_attr
    def __tablename__(cls):
        return p.plural(cls.__name__.lower())


Base = declarative_base(cls=Base)


class User(IDMixin, TimestampsMixin, Base):
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String, nullable=False, default=settings.default_avatar_url)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    followers_count: Mapped[int] = mapped_column(default=0, nullable=False)
    subscriptions_count: Mapped[int] = mapped_column(default=0, nullable=False)
