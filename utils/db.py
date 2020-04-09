from typing import List

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from database import models


def get_user(db: Session, user_id: int) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_nickname(db: Session, nickname: str) -> models.User:
    return db.query(models.User).filter(models.User.nickname == nickname).first()


def get_recipe(db: Session, recipe_id: int) -> models.Recipe:
    return db.query(and_(models.Recipe.id == recipe_id, models.Recipe.is_active == True)).first()


def get_recipes(db: Session) -> List[models.Recipe]:
    return db.query(models.Recipe).filter(models.Recipe.is_active == True).all()


def get_recipe_for_admin(db: Session, recipe_id: int) -> models.Recipe:
    return db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()


def get_recipes_by_id(db: Session, recipes_id: list) -> List[models.Recipe]:
    return db.query(models.Recipe).filter(and_(models.Recipe.id.in_(recipes_id), models.Recipe.is_active == True)).all()


def get_recipes_by_user(db: Session, user_id: int) -> List[models.Recipe]:
    return db.query(models.Recipe).filter(and_(models.Recipe.author_id == user_id, models.Recipe.is_active == True)).all()


def get_recipe_hashtag(db: Session, hashtag_id: int) -> List[models.RecipeHashtag]:
    return db.query(models.RecipeHashtag).filter(models.RecipeHashtag.tag_id == hashtag_id).all()


def get_hashtag(db: Session, tag: str) -> models.Hashtag:
    return db.query(models.Hashtag).filter(models.Hashtag.tag == tag).first()


def get_hashtags(db: Session) -> List[models.Hashtag]:
    return db.query(models.Hashtag).all()


def get_hashtags_by_tags(db: Session, tags: list) -> List[models.Hashtag]:
    return db.query(models.Hashtag).filter(models.Hashtag.tag.in_(tags)).all()


def get_likes_by_user(db: Session, user_id: int) -> List[models.Likes]:
    return db.query(models.Likes).filter(models.Likes.user_id == user_id).all()


def get_likes_by_user_recipe(db: Session, user_id: int, recipe_id: int) -> List[models.Likes]:
    return db.query(models.Likes).filter(
        and_(models.Likes.user_id == user_id, models.Likes.recipe_id == recipe_id)).first()


def get_top_likes(db: Session, limit: int) -> List[models.Likes]:
    return db.query(models.Likes.recipe_id, func.count(models.Likes.id)).order_by(
        desc(func.count(models.Likes.id))).group_by(models.Likes.recipe_id).limit(limit).all()
