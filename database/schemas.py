from datetime import date
from typing import List

from pydantic import BaseModel


class LikeBase(BaseModel):
    user_id: int
    recipe_id: int


class LikeCreate(LikeBase):
    pass


class Like(LikeBase):
    id: int

    class Config:
        orm_mode = True


class RecipeHashtagBase(BaseModel):
    tag_id: int
    recipe_id: int


class RecipeHashtagCreate(RecipeHashtagBase):
    pass


class RecipeHashtag(RecipeHashtagBase):
    id: int

    class Config:
        orm_mode = True


class RecipeBase(BaseModel):
    name: str
    description: str
    steps_making: str
    type: str
    is_active: bool = True
    date_creation: date


class RecipeCreate(RecipeBase):
    author_id: int


class RecipeChange(BaseModel):
    name: str = None
    description: str = None
    steps_making: str = None
    type: str = None


class RecipeShow(RecipeBase):
    id: int
    photo: str = None
    author: str
    likes: int
    tags: list


class Recipe(RecipeBase):
    id: int
    photo: str
    author_id: int
    recipe_likes: List[Like] = []
    tags: List[RecipeHashtag] = []

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    nickname: str


class UserCreate(UserBase):
    password: str


class UserShow(UserBase):
    id: int = None
    is_active: bool


class User(UserShow):
    hashed_password: str
    role: str

    my_recipe: List[Recipe] = []
    user_likes: List[Like] = []

    class Config:
        orm_mode = True


class HashtagBase(BaseModel):
    tag: str


class HashtagCreate(HashtagBase):
    pass


class Hashtag(HashtagBase):
    id: int
    recipe: List[RecipeHashtag]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
