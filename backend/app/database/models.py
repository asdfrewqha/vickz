from typing import Optional
from uuid import UUID

import inflect
from app.core.settings import settings
from app.database.mixins.id_mixins import IDMixin, RandomIDMixin
from app.database.mixins.timestamp_mixins import CreatedAtMixin, TimestampsMixin
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    declared_attr,
    mapped_column,
    relationship,
)

p = inflect.engine()


class Base:
    @declared_attr
    def __tablename__(cls):
        return p.plural(cls.__name__.lower())


Base = declarative_base(cls=Base)


class CommentLike(RandomIDMixin, CreatedAtMixin, Base):
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    comment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("comments.id", ondelete="CASCADE"),
    )
    like: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="like_user_comment_uc"),)


class Comment(IDMixin, CreatedAtMixin, Base):
    video_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    user_username: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    parent_username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    likes: Mapped[int] = mapped_column(default=0, nullable=False)
    dislikes: Mapped[int] = mapped_column(default=0, nullable=False)
    replies_count: Mapped[int] = mapped_column(default=0, nullable=False)

    user = relationship("User", back_populates="comments")
    video = relationship("Video", back_populates="comment_list")
    comm_likers = relationship("CommentLike", backref="comment", cascade="all, delete")

    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment",
        remote_side=lambda: [Comment.id],
        backref="replies",
    )


class Subscription(CreatedAtMixin, Base):
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
    subscribed_to = relationship(
        "User", foreign_keys=[subscribed_to_id], back_populates="subscribers"
    )

    __table_args__ = (
        UniqueConstraint("subscriber_id", "subscribed_to_id", name="subscription_uc"),
    )


class Like(RandomIDMixin, CreatedAtMixin, Base):
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    video_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("videos.id", ondelete="CASCADE"))
    like: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user = relationship("User", back_populates="likes")

    __table_args__ = (UniqueConstraint("user_id", "video_id", name="like_user_video_uc"),)


class View(RandomIDMixin, CreatedAtMixin, Base):
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    video_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("videos.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="views")


class User(IDMixin, TimestampsMixin, Base):
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str] = mapped_column(
        String, nullable=False, default=settings.default_avatar_url
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    followers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscriptions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subscriptions = relationship(
        "Subscription",
        foreign_keys=[Subscription.subscriber_id],
        back_populates="subscriber",
        cascade="all, delete-orphan",
    )

    subscribers = relationship(
        "Subscription",
        foreign_keys=[Subscription.subscribed_to_id],
        back_populates="subscribed_to",
        cascade="all, delete-orphan",
    )

    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    views = relationship("View", back_populates="user", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="author", cascade="all, delete")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    comment_likes = relationship("CommentLike", backref="user", cascade="all, delete-orphan")


class Video(TimestampsMixin, Base):
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    author_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    views: Mapped[int] = mapped_column(default=0)
    likes: Mapped[int] = mapped_column(default=0)
    dislikes: Mapped[int] = mapped_column(default=0)
    comments: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")

    author = relationship("User", back_populates="videos")
    comment_list = relationship("Comment", back_populates="video", cascade="all, delete-orphan")
    likes_list = relationship("Like", backref="video", cascade="all, delete-orphan")
