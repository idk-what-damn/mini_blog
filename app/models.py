from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
from app.database import Base
from sqlalchemy.orm import validates
import re

pwd_context = CryptContext(
    schemes=["sha256_crypt"],
    deprecated="auto"
)
article_tags = Table('article_tags', Base.metadata,
                     Column('article_id', Integer, ForeignKey('articles.id')),
                     Column('tag_id', Integer, ForeignKey('tags.id'))
                     )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    articles = relationship("Article", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    @validates('username')
    def validate_username(self, key, username):
        if len(username) < 3:
            raise ValueError("Имя пользователя должно содержать минимум 3 символа")
        if len(username) > 50:
            raise ValueError("Имя пользователя не должно превышать 50 символов")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Имя пользователя может содержать только буквы, цифры и символ подчеркивания")
        return username

    @validates('email')
    def validate_email(self, key, email):
        if '@' not in email:
            raise ValueError("Некорректный email адрес")
        return email

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship("User", back_populates="articles")
    comments = relationship("Comment", back_populates="article")
    tags = relationship("Tag", secondary=article_tags, back_populates="articles")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    articles = relationship("Article", secondary=article_tags, back_populates="tags")
