from fastapi import status, Body, APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from database import schemas
from database.database import get_db
from service import user
from utils import auth

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.UserShow)
def create_user(user_data: schemas.UserCreate = Body(
    ...,
    example={
        "nickname": "nick",
        "password": "password"
    }), db: Session = Depends(get_db)):
    db_user = user.registration(db, user_data, 'user')
    if not db_user.id:
        raise HTTPException(status_code=400, detail="Nickname already registered")
    return schemas.UserShow(id=db_user.id, nickname=db_user.nickname, is_active=db_user.is_active)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=schemas.Token)
async def login(user_data: schemas.UserCreate = Body(
    ...,
    example={
        "nickname": "nick",
        "password": "password"
    }), db: Session = Depends(get_db)):
    token = user.login(db, user_data)
    if 'error' in token.keys():
        raise HTTPException(status_code=400, detail=token['error'])
    return token


@router.get("")
def user_profile(jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    return user.get_profile(db, db_user.id)


@router.put('/{user_id}/ban', status_code=status.HTTP_200_OK, response_model=schemas.UserShow)
def ban_recipe(user_id: str, jwt: str = Header(..., example='key'),
               db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    if db_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access")
    try:
        db_user = user.ban_user(db, int(user_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid user_id must be a number')
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='There is no such user')
    return schemas.UserShow(id=db_user.id, nickname=db_user.nickname, is_active=db_user.is_active)


@router.delete('/{user_id}', status_code=status.HTTP_200_OK)
def delete_user(user_id: str, jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    if db_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access")
    try:
        db_recipe = user.delete_user(db, int(user_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid recipe_id must be a number')
    if db_recipe is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='There is no such recipe')
    return {'detail': f'The user ({user_id}) was deleted'}