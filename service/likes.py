from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import models, schemas
from utils.db import get_likes_by_user_recipe


def like_it(db: Session, like: schemas.LikeCreate) -> models.Likes:
    """Like and add to the user's favorites

    :param db: database connection
    :param like: info about like (user id and recipe id)
    :return: object Likes
    """
    likes = get_likes_by_user_recipe(db, like.user_id, like.recipe_id)
    print(likes)
    db_like = models.Likes(**like.dict())
    try:
        if likes is not None:
            db.query(models.Likes.id).filter_by(id=likes.id).delete()
        else:
            db.add(db_like)
        db.commit()
        db.refresh(db_like)
    except IntegrityError:
        db.rollback()
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    print(db_like)
    return db_like
