from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text, Date, UniqueConstraint
from sqlalchemy.orm import relationship

from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)

    my_recipe = relationship("Recipe", back_populates="author")
    user_likes = relationship("Likes", back_populates="user")


    def __str__(self):
        return f"id={self.id} | nickname={self.nickname} | hashed_password={self.hashed_password} | " \
               f"is_active={self.is_active} | role={self.role} | my_recipe={self.my_recipe} | " \
               f"user_likes={self.user_likes}"

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    description = Column(String)
    steps_making = Column(Text)
    photo = Column(String)
    type = Column(String)
    is_active = Column(Boolean, default=True)
    date_creation = Column(Date)

    author = relationship("User", back_populates="my_recipe")
    recipe_likes = relationship("Likes", back_populates="recipe")
    tags = relationship("RecipeHashtag", back_populates="recipe")


    def __str__(self):
        return f"id={self.id} | author_id={self.author_id} | name={self.name} | description={self.description} | " \
               f"steps_making={self.steps_making} | photo={self.photo} | type={self.type} | is_active={self.is_active} | " \
               f"date_creation={self.date_creation} | author={self.author} | recipe_likes={self.recipe_likes} | " \
               f"tags={self.tags}"

class Hashtag(Base):
    __tablename__ = "hashtags"

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, unique=True, index=True)

    recipe = relationship("RecipeHashtag", back_populates="tag")

    def __str__(self):
        return f"id={self.id} | tag={self.tag} | recipe={self.recipe}"

class RecipeHashtag(Base):
    __tablename__ = "recipe_hashtags"
    __table_args__ = (UniqueConstraint('tag_id', 'recipe_id', name='unique_tag'),)
    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey("hashtags.id"), index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), index=True)

    tag = relationship("Hashtag", back_populates="recipe")
    recipe = relationship("Recipe", back_populates="tags")

    def __str__(self):
        return f"id={self.id} | tag_id={self.tag_id} | recipe_id={self.recipe_id} | tag={self.tag} | " \
               f"recipe={self.recipe}"

class Likes(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint('user_id', 'recipe_id', name='unique_likes'),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), index=True)

    recipe = relationship("Recipe", back_populates="recipe_likes")
    user = relationship("User", back_populates="user_likes")

    def __str__(self):
        return f"id={self.id} | user_id={self.user_id} | recipe_id={self.recipe_id} | recipe={self.recipe} | " \
               f"user={self.user}"