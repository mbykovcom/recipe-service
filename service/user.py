from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import Config
from database import schemas
from database import models
from utils.auth import get_password_hash, verify_password, create_access_token
from utils.db import get_user_by_nickname, get_user


def registration(db: Session, user_data: schemas.UserCreate, role: str = 'user') -> models.User:
    """Registration new a user

    :param db: database connection
    :param user_data: object UserCreate with data a user for registration
    :param role: role the user in the app
    :return: data the user
    """
    hashed_password = get_password_hash(user_data.password)
    new_user = models.User(nickname=user_data.nickname, hashed_password=hashed_password, is_active=True, role=role)
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        print(f'Error: This nickname ({user_data.nickname}) is busy')
        db.rollback()
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()

    return new_user


def login(db: Session, user_data: schemas.UserCreate) -> dict:
    """User authorization

    :param db: database connection
    :param user_data: object UserCreate with data a user for login
    :return: Dictionary with access token and token type
    """
    db_user = get_user_by_nickname(db, user_data.nickname)
    if db_user:
        if verify_password(user_data.password, db_user.hashed_password):
            access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_data.nickname}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            return {'error': 'Invalid password'}
    return {'error': 'Invalid username'}


def get_profile(db: Session, user_id: int) -> dict:
    """Get user profile

    :param db: database connection
    :param user_id: user id
    :return: Dictionary with info about the user
    """
    db_user = get_user(db, user_id)
    if db_user:
        profile = {
            'id': db_user.id,
            'nickname': db_user.nickname,
            'is_active': db_user.is_active,
            'favorites': [like.recipe_id for like in db_user.user_likes],
            'number_my_recipe': len(db_user.my_recipe)
        }
        return profile
    else:
        return {'error': 'The user does not exist'}


def ban_user(db: Session, user_id: int) -> models.User:
    """Prohibit the user from adding their own recipes

    :param db: database connection
    :param user_id: user id
    :return: object User with data the user
    """
    user_data = get_user(db, user_id)
    user_data.is_active = not user_data.is_active
    try:
        db.add(user_data)
        db.commit()
        db.refresh(user_data)
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    return user_data


def delete_user(db: Session, user_id: int) -> bool:
    """Delete user

    :param db: database connection
    :param user_id: user id
    :return: the result of the removal
    """
    user_data = get_user(db, user_id)
    if user_data is None:
        return False
    try:
        db.delete(user_data)
        db.commit()
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    return True
