from uuid import UUID
import inflect

from sqlalchemy import Integer, String, Uuid, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, declared_attr, relationship

from app.database.mixins.id_mixins import IDMixin
from app.database.mixins.timestamp_mixins import TimestampsMixin, CreatedAtMixin
from app.core.settings import settings

p = inflect.engine()


class Base:
    @declared_attr
    def __tablename__(cls):
        return p.plural(cls.__name__.lower())


Base = declarative_base(cls=Base)


class Subscription(CreatedAtMixin, Base):
    __tablename__ = "subscriptions"

    subscriber_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    subscribed_to_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    subscriber = relationship("User", foreign_keys=[subscriber_id], back_populates="subscriptions")
    subscribed_to = relationship("User", foreign_keys=[subscribed_to_id], back_populates="subscribers")


class User(IDMixin, TimestampsMixin, Base):
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String, nullable=False, default=settings.default_avatar_url)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    followers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscriptions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subscriptions = relationship(
        "Subscription",
        foreign_keys="[Subscription.subscriber_id]",
        back_populates="subscriber",
        cascade="all, delete-orphan",
    )

    subscribers = relationship(
        "Subscription",
        foreign_keys="[Subscription.subscribed_to_id]",
        back_populates="subscribed_to",
        cascade="all, delete-orphan",
    )
