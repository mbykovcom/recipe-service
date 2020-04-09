from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from database import models
from database.models import Recipe
from database import schemas
from service import hashtag
from utils.db import get_recipes, get_hashtags_by_tags, get_recipe_hashtag, get_top_likes, \
    get_recipes_by_id, get_recipes_by_user, get_recipe_for_admin


def create_recipe(db: Session, recipe: schemas.RecipeCreate, author_id: int, tags: list) -> Recipe:
    """Create new a recipe

    :param db: database connection
    :param recipe: object RecipeCreate with data a recipe for create
    :param author_id: creator id
    :return: data the recipe
    """
    hashtag.create_hashtag(db, tags)
    recipe.author_id = author_id
    new_recipe = models.Recipe(**recipe.dict())
    try:
        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()

    hashtag.create_recipe_hashtags(db, new_recipe.id, tags)
    db.refresh(new_recipe)
    return new_recipe


def add_photo(db: Session, recipe_id: int, url_photo: str) -> Recipe:
    """Add a photo to the recipe

    :param db: database connection
    :param recipe_id: recipe id
    :param url_photo: path to the photo on the server
    :return: data the recipe
    """
    recipe = get_recipes_by_id(db, [recipe_id])[0]
    recipe.photo = url_photo
    try:
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    return recipe


def get_recipe_by_filter(db: Session, name: str = None, type: str = None, tag: str = None) -> List[Recipe]:
    """Get recipes by filter. If no filters are set all recipes are returned.

    :param db: database connection
    :param name: recipe name
    :param type: recipe type
    :param tag: recipe hashtags
    :return: list with recipe
    """
    if name and type and tag:
        tag_id = get_hashtags_by_tags(db, [tag])[0].id
        recipe_id = [recipe.recipe_id for recipe in get_recipe_hashtag(db, tag_id)]
        recipes = db.query(models.Recipe).filter(and_(
            models.Recipe.name.ilike(f"%{name}%"),
            models.Recipe.type == type,
            models.Recipe.id.in_(recipe_id)
        )).all()
    elif name and type:
        recipes = db.query(models.Recipe).filter(and_(
            models.Recipe.name.ilike(f"%{name}%"),
            models.Recipe.type == type
        )).all()
    elif name and tag:
        tag_id = get_hashtags_by_tags(db, [tag])[0].id
        recipe_id = [recipe.recipe_id for recipe in get_recipe_hashtag(db, tag_id)]
        recipes = db.query(models.Recipe).filter(and_(
            models.Recipe.name.ilike(f"%{name}%"),
            models.Recipe.id.in_(recipe_id)
        )).all()
    elif type and tag:
        tag_id = get_hashtags_by_tags(db, [tag])[0].id
        recipe_id = [recipe.recipe_id for recipe in get_recipe_hashtag(db, tag_id)]
        recipes = db.query(models.Recipe).filter(and_(
            models.Recipe.type == type,
            models.Recipe.id.in_(recipe_id)
        )).all()
    elif name:
        recipes = db.query(models.Recipe).filter(models.Recipe.name.ilike(f"%{name}%")).all()
    elif type:
        recipes = db.query(models.Recipe).filter(models.Recipe.type == type).all()
    elif tag:
        tag_id = get_hashtags_by_tags(db, [tag])[0].id
        recipe_id = [recipe.recipe_id for recipe in get_recipe_hashtag(db, tag_id)]
        recipes = db.query(models.Recipe).filter(models.Recipe.id.in_(recipe_id)).all()
    else:
        recipes = get_recipes(db)
    return recipes


def get_top_recipe(db: Session, limit: int) -> List[models.Recipe]:
    """Get top recipes

    :param db: database connection
    :param limit: number of recipes to output
    :return: list with recipe
    """
    top_recipe = get_top_likes(db, limit)
    top_recipe = [like[0] for like in top_recipe]
    recipe_list = get_recipes_by_id(db, top_recipe)
    return recipe_list


def get_user_recipes(db: Session, user_id: int) -> List[models.Recipe]:
    """Get recipes that belongs to the user

    :param db: database connection
    :param user_id: user id
    :return: list with recipe
    """
    return get_recipes_by_user(db, user_id)


def change_recipe(db: Session, recipe_id: int, recipe: schemas.RecipeChange, user_id: int) -> models.Recipe:
    """Change a recipe

    :param db: database connection
    :param recipe_id: recipe id
    :param recipe: new recipe data
    :param user_id: user id
    :return: data updated recipe
    """
    my_recipes = [recipe.id for recipe in get_user_recipes(db, user_id)]
    if recipe_id not in my_recipes:
        return None
    recipe_data = get_recipes_by_id(db, [recipe_id])[0]
    if recipe.name:
        recipe_data.name = recipe.name
    if recipe.description:
        recipe_data.description = recipe.description
    if recipe.steps_making:
        recipe_data.steps_making = recipe.steps_making
    if recipe.type:
        recipe_data.type = recipe.type
    try:
        db.add(recipe_data)
        db.commit()
        db.refresh(recipe_data)
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    return recipe_data


def ban_recipe(db: Session, recipe_id: int) -> models.Recipe:
    """Hide a recipe from users

    :param db: database connection
    :param recipe_id: recipe id
    :return: data updated recipe
    """
    recipe_data = get_recipe_for_admin(db, recipe_id)
    recipe_data.is_active = not recipe_data.is_active
    try:
        db.add(recipe_data)
        db.commit()
        db.refresh(recipe_data)
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    return recipe_data


def delete_recipe(db: Session, recipe_id: int) -> bool:
    """Delete user

    :param db: database connection
    :param recipe_id: recipe id
    :return: the result of the removal
    """
    recipe_data = get_recipe_for_admin(db, recipe_id)
    if recipe_data is None:
        return False
    try:
        db.delete(recipe_data)
        db.commit()
    except BaseException as e:
        print(f'Error: {e}')
        db.rollback()
    return True