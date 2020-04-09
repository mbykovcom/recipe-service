from typing import List

from sqlalchemy.orm import Session

from database import models
from utils.db import get_hashtags, get_hashtags_by_tags


def create_hashtag(db: Session, tags: list) -> List[models.Hashtag]:
    hashtags_db = get_hashtags(db)
    hashtags_set = set([hashtag.tag for hashtag in hashtags_db])
    tags = set(tags) - hashtags_set
    hashtags = []
    for tag in tags:
        hashtags.append(models.Hashtag(tag=tag))
    try:
        db.add_all(hashtags)
        db.commit()
        db.refresh(hashtags)
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()

    return hashtags


def create_recipe_hashtags(db: Session, recipe_id: int, hashtags: List[str]) -> List[models.RecipeHashtag]:
    hashtags_db = get_hashtags_by_tags(db, hashtags)
    hashtags_list = []
    for hashtag in hashtags_db:
        hashtags_list.append(models.RecipeHashtag(tag_id=hashtag.id, recipe_id=recipe_id))
    try:
        db.add_all(hashtags_list)
        db.commit()
        db.refresh(hashtags_list)
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    return hashtags_list
