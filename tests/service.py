import unittest
from datetime import datetime
from typing import List

from database.database import SessionLocal
from database import schemas, models
from service import user, recipe, hashtag, likes
from utils import db


class TestService:
    def setup_class(cls):
        cls.db = SessionLocal()

        cls.new_user = schemas.UserCreate(nickname='nickname', password='pass')
        cls.user: models.User = None

        cls.new_recipe = schemas.RecipeCreate(name='Recipe', description='Description',
                                              steps_making='1. asdfasdf 2.asdasd', type='Десерт',
                                              is_active=True, tags=['tag1', 'tag2'],
                                              date_creation='2020-04-09', author_id=0)
        cls.recipe: models.Recipe = None
        cls.photo = None

        cls.tags = ['Cake', 'Chocolate', 'Cream']
        cls.hashtags: List[models.Hashtag] = None

    def teardown_class(cls):
        cls.db.query(models.Likes).delete()
        cls.db.query(models.RecipeHashtag).delete()
        cls.db.query(models.Recipe).delete()
        cls.db.query(models.User).delete()
        cls.db.query(models.Hashtag).delete()
        cls.db.commit()
        cls.db.close()

    def test_registration(self):
        user_data = user.registration(self.db, self.new_user, 'user')
        assert type(user_data) is models.User
        assert type(user_data.id) is int
        TestService.user = user_data

    def test_registration_again(self):
        user_data = user.registration(self.db, self.new_user, 'user')
        assert type(user_data) is models.User
        assert user_data.id is None

    def test_login(self):
        jwt = user.login(self.db, self.new_user)
        assert 'access_token' in jwt.keys()

    def test_login_invalid_nick(self):
        invalid_user = schemas.UserCreate(nickname='invalid', password=self.new_user.password)
        jwt = user.login(self.db, invalid_user)
        assert jwt == {'error': 'Invalid username'}

    def test_login_invalid_password(self):
        invalid_user = schemas.UserCreate(nickname=self.new_user.nickname, password='invalid')
        jwt = user.login(self.db, invalid_user)
        assert jwt == {'error': 'Invalid password'}

    def test_get_profile(self):
        profile = user.get_profile(self.db, self.user.id)
        assert profile == {
            'id': self.user.id,
            'nickname': self.user.nickname,
            'is_active': self.user.is_active,
            'favorites': [],
            'number_my_recipe': 0
        }

    def test_get_profile_doest_exists(self):
        profile = user.get_profile(self.db, -1)
        assert profile == {'error': 'The user does not exist'}

    def test_create_hashtags(self):
        TestService.hashtags = hashtag.create_hashtag(self.db, [self.tags[0], self.tags[1]])
        assert self.hashtags[0].tag in self.tags
        assert type(self.hashtags[0].id) is int
        assert self.hashtags[1].tag in self.tags
        assert type(self.hashtags[1].id) is int

    def test_create_recipe(self):
        db_recipe = recipe.create_recipe(self.db, self.new_recipe, self.user.id, self.tags)
        assert type(db_recipe) is models.Recipe
        assert type(db_recipe.id) is int
        TestService.recipe = db_recipe

    def test_get_recipes(self):
        recipes = db.get_recipes(self.db)
        assert recipes[0].id == self.recipe.id

    def test_get_recipe_by_filter(self):
        recipe_1 = schemas.RecipeCreate(name='Re 2', description='Description',
                                        steps_making='1. asdfasdf 2.asdasd',
                                        photo='/usr/src/images/image.jpg', type='Десерт', is_active=True,
                                        date_creation=datetime.today(), author_id=0)
        recipe.create_recipe(self.db, recipe_1, self.user.id, ['lemon', 'Chocolate'])
        recipe_2 = schemas.RecipeCreate(name='Vodka', description='Description',
                                        steps_making='1. asdfasdf 2.asdasd',
                                        photo='/usr/src/images/image.jpg', type='Напиток', is_active=True,
                                        date_creation=datetime.today(), author_id=0)
        db_recipe = recipe.create_recipe(self.db, recipe_2, self.user.id, ['drink', 'alcohol'])
        recipes = recipe.get_recipe_by_filter(self.db)
        assert len(recipes) == 3
        recipes = recipe.get_recipe_by_filter(self.db, name='Recipe')
        assert len(recipes) == 1
        assert recipes[0].name == "Recipe"
        recipes = recipe.get_recipe_by_filter(self.db, type='Десерт')
        assert len(recipes) == 2
        recipes = recipe.get_recipe_by_filter(self.db, tag='drink')
        assert len(recipes) == 1
        assert recipes[0].name == "Vodka"
        recipes = recipe.get_recipe_by_filter(self.db, type='Десерт', tag='lemon')
        assert len(recipes) == 1
        assert recipes[0].name == 'Re 2'
        recipes = recipe.get_recipe_by_filter(self.db, name='re', tag='Chocolate')
        assert len(recipes) == 2
        recipes = recipe.get_recipe_by_filter(self.db, name='recipe', type='Десерт')
        assert len(recipes) == 1
        assert recipes[0].name == "Recipe"
        recipes = recipe.get_recipe_by_filter(self.db, name='re', type='Десерт', tag='Chocolate')
        assert len(recipes) == 2

    def test_like_it(self):
        like = schemas.LikeCreate(user_id=self.user.id, recipe_id=self.recipe.id)
        like_it = likes.like_it(self.db, like)
        assert like_it.id is not None
        like_it = likes.like_it(self.db, like)
        assert like_it.id is None

    def test_get_top_recipe(self):
        like = schemas.LikeCreate(user_id=self.user.id, recipe_id=self.recipe.id + 1)
        likes.like_it(self.db, like)
        user_ = schemas.UserCreate(nickname='name', password='pass')
        user_data = user.registration(self.db, user_, 'user')
        like.user_id = user_data.id
        likes.like_it(self.db, like)
        like.recipe_id = self.recipe.id
        likes.like_it(self.db, like)
        top = recipe.get_top_recipe(self.db, 2)
        assert top[0].id == self.recipe.id

    def test_ban_recipe(self):
        recipes_before = db.get_recipes(self.db)
        data_recipe = recipe.ban_recipe(self.db, self.recipe.id)
        assert data_recipe.is_active is False
        recipes_after = db.get_recipes(self.db)
        assert set(recipes_before) != set(recipes_after)
        data_recipe = recipe.ban_recipe(self.db, self.recipe.id)
        assert data_recipe.is_active is True
        recipes_after = db.get_recipes(self.db)
        assert set(recipes_before) == set(recipes_after)

    def test_ban_user(self):
        user_data = user.ban_user(self.db, self.user.id)
        assert user_data.is_active is False
        user_data = user.ban_user(self.db, self.user.id)
        assert user_data.is_active is True

    def test_delete_recipe(self):
        result = recipe.delete_recipe(self.db, self.recipe.id)
        assert result is True
        resipes_id = [db_recipe.id for db_recipe in recipe.get_recipes(self.db)]
        assert self.recipe.id not in resipes_id

    def test_delete_user(self):
        result = user.delete_user(self.db, self.user.id)
        assert result is True
        db_user = user.get_user(self.db, self.user.id)
        assert db_user is None


if __name__ == '__main__':
    unittest.main()
