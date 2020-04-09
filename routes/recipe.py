import os
from datetime import datetime
from typing import List

from fastapi import status, Body, APIRouter, HTTPException, Depends, Header, UploadFile, File
from sqlalchemy.orm import Session

from database import schemas
from database.database import get_db
from service import recipe, likes, user
from utils import auth
from config import Config

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.RecipeShow)
def create_recipe(recipe_data: schemas.RecipeCreate = Body(
    ...,
    example={
        'name': 'Recipe',
        'description': 'Description',
        'steps_making': '1. Step one 2. Step two',
        'type': 'drink',
        'is_active': True,
        'date_creation': datetime.today().date(),
        'author_id': 1}), tags=Body(..., example={'tags': ['tag1', 'tag2']}),
        jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    if not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                            detail='You don`t have permission to create a recipe')
    if recipe_data.type not in Config.TYPES_RECIPE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid recipe type')
    db_recipe = recipe.create_recipe(db, schemas.RecipeCreate(**recipe_data.dict()), db_user.id, tags)
    return schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                              steps_making=db_recipe.steps_making, type=db_recipe.type,
                              tags=[tag.tag.tag for tag in db_recipe.tags],
                              likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                              date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                              author=db_recipe.author.nickname)


@router.put("/{recipe_id}", status_code=status.HTTP_200_OK, response_model=schemas.RecipeShow)
def change_recipe(recipe_id: str, recipe_data: schemas.RecipeChange = Body(
    ...,
    example={
        'name': 'Recipe',
        'description': 'Description',
        'steps_making': '1. Step one 2. Step two',
        'type': 'Десерт'}), jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    db_recipe = recipe.change_recipe(db, int(recipe_id), schemas.RecipeChange(**recipe_data.dict()), db_user.id)
    if db_recipe is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='The user does not have a recipe with this ID')
    return schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                              steps_making=db_recipe.steps_making, type=db_recipe.type,
                              tags=[tag.tag.tag for tag in db_recipe.tags],
                              likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                              date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                              author=db_recipe.author.nickname)


@router.post("/{recipe_id}", status_code=status.HTTP_201_CREATED, response_model=schemas.RecipeShow)
def add_photo(recipe_id: str, photo: UploadFile = File(...), jwt: str = Header(..., example='key'),
              db: Session = Depends(get_db)):
    auth.get_current_user(jwt)
    file_extension = photo.filename.split('.')[1]
    if file_extension not in ['jpg', 'jpeg', 'png']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid file extension')
    url_photo = f"{Config.BASE_DIR_IMAGES}/{recipe_id}_{photo.filename}"
    with open(url_photo, 'wb') as f:
        f.write(photo.file.read())
    db_recipe = recipe.add_photo(db, int(recipe_id), url_photo)
    return schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                              steps_making=db_recipe.steps_making, type=db_recipe.type,
                              tags=[tag.tag.tag for tag in db_recipe.tags],
                              likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                              date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                              author=db_recipe.author.nickname)


@router.get("", status_code=status.HTTP_200_OK, response_model=List[schemas.RecipeShow])
def get_recipes(jwt: str = Header(..., example='key'), name: str = None, type: str = None, tag: str = None,
                db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    recipes = recipe.get_recipe_by_filter(db, name, type, tag)
    return [schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                               steps_making=db_recipe.steps_making, type=db_recipe.type,
                               tags=[tag.tag.tag for tag in db_recipe.tags],
                               likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                               date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                               author=db_recipe.author.nickname) for db_recipe in recipes]


@router.get('/top', status_code=status.HTTP_200_OK, response_model=List[schemas.RecipeShow])
def get_top_recipes(limit: int = 10, jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    recipes = recipe.get_top_recipe(db, limit)
    return [schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                               steps_making=db_recipe.steps_making, type=db_recipe.type,
                               tags=[tag.tag.tag for tag in db_recipe.tags],
                               likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                               date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                               author=db_recipe.author.nickname) for db_recipe in recipes]


@router.post('/{recipe_id}/like', status_code=status.HTTP_200_OK)
def like_recipe(recipe_id: str, jwt: str = Header(..., example='key'),
                db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    try:
        like = schemas.LikeCreate(user_id=db_user.id, recipe_id=int(recipe_id))
        db_like = likes.like_it(db, like)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid recipe_id must be a number')
    if db_like.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='There is no such recipe')
    profile = user.get_profile(db, db_user.id)
    return {'user_id': profile['id'], 'favorites': profile['favorites']}


@router.get('/like', status_code=status.HTTP_200_OK, response_model=List[schemas.RecipeShow])
def get_favorites_recipe(jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    favorites = user.get_profile(db, db_user.id)['favorites']
    recipes = recipe.get_recipes_by_id(db, favorites)
    return [schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                               steps_making=db_recipe.steps_making, type=db_recipe.type,
                               tags=[tag.tag.tag for tag in db_recipe.tags],
                               likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                               date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                               author=db_recipe.author.nickname) for db_recipe in recipes]


@router.get('/my', status_code=status.HTTP_200_OK, response_model=List[schemas.RecipeShow])
def get_my_recipes(jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    my_recipe = recipe.get_user_recipes(db, db_user.id)
    return [schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                               steps_making=db_recipe.steps_making, type=db_recipe.type,
                               tags=[tag.tag.tag for tag in db_recipe.tags],
                               likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                               date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                               author=db_recipe.author.nickname) for db_recipe in my_recipe]


@router.put('/{recipe_id}/ban', status_code=status.HTTP_200_OK, response_model=schemas.RecipeShow)
def ban_recipe(recipe_id: str, jwt: str = Header(..., example='key'),
               db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    if db_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access")
    try:
        db_recipe = recipe.ban_recipe(db, int(recipe_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid recipe_id must be a number')
    if db_recipe is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='There is no such recipe')
    return schemas.RecipeShow(id=db_recipe.id, name=db_recipe.name, description=db_recipe.description,
                              steps_making=db_recipe.steps_making, type=db_recipe.type,
                              tags=[tag.tag.tag for tag in db_recipe.tags],
                              likes=len(db_recipe.recipe_likes), is_active=db_recipe.is_active,
                              date_creation=db_recipe.date_creation, photo=db_recipe.photo,
                              author=db_recipe.author.nickname)


@router.delete('/{recipe_id}', status_code=status.HTTP_200_OK)
def delete_recipe(recipe_id: str, jwt: str = Header(..., example='key'), db: Session = Depends(get_db)):
    db_user = auth.get_current_user(jwt)
    if db_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access")
    try:
        db_recipe = recipe.delete_recipe(db, int(recipe_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid recipe_id must be a number')
    if db_recipe is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='There is no such recipe')
    return {'detail': f'The recipe ({recipe_id}) was deleted'}