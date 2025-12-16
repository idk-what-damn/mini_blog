from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
import re


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: int

    class Config:
        from_attributes = True



class Token(BaseModel):
    access_token: str
    token_type: str



class ArticleBase(BaseModel):
    title: str
    content: str


class ArticleCreate(ArticleBase):
    tag_names: Optional[List[str]] = []


class ArticleResponse(ArticleBase):
    id: int
    author_id: int
    created_at: datetime
    author: Optional[UserResponse] = None

    class Config:
        from_attributes = True



class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: int
    article_id: int
    author_id: int
    created_at: datetime
    author: Optional[UserResponse] = None

    class Config:
        from_attributes = True



class TagBase(BaseModel):
    name: str


class TagResponse(TagBase):
    id: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    current_password: str
    new_password: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError("Имя пользователя должно содержать минимум 3 символа")
            if len(v) > 50:
                raise ValueError("Имя пользователя не должно превышать 50 символов")
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError("Имя пользователя может содержать только буквы, цифры и символ подчеркивания")
        return v

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v
