import os
import time
import unittest
from datetime import datetime
from typing import List

from fastapi import UploadFile
from fastapi.testclient import TestClient

from app import app
from database import schemas, models
from database.database import SessionLocal
from service import user

client = TestClient(app)

basedir = os.path.abspath(os.path.dirname(__file__))


class TestRoutes:

    def setup_class(cls):
        cls.db = SessionLocal()

        cls.new_user = {'nickname': 'nick', 'password': 'pass'}
        cls.new_recipe = {'name': 'Recipe', 'description': 'Description', 'steps_making': '1. asdfasdf 2.asdasd',
                          'type': 'dessert', 'is_active': True, 'date_creation': '2020-04-09', 'author_id': 0}
        cls.recipe_id = None
        cls.user_id = None
        cls.jwt = {'user': None}

        cls.new_admin = {'nickname': 'admin', 'password': 'admin'}
        cls.admin = user.registration(cls.db, schemas.UserCreate(**cls.new_admin), 'admin')

    def teardown_class(cls):
        cls.db.query(models.Likes).delete()
        cls.db.query(models.RecipeHashtag).delete()
        cls.db.query(models.Recipe).delete()
        cls.db.query(models.User).delete()
        cls.db.query(models.Hashtag).delete()
        cls.db.commit()
        cls.db.close()

    def test_create_user(self):
        response = client.post('/user', json=self.new_user)
        assert response.status_code == 201
        response = response.json()
        assert response == {'nickname': self.new_user['nickname'], 'id': response['id'], 'is_active': True}

    def test_create_user_again(self):
        response = client.post('/user', json=self.new_user)
        assert response.status_code == 400
        assert response.json() == {'detail': 'Nickname already registered'}

    def test_login_user(self):
        response = client.post('/user/login', json=self.new_user)
        assert response.status_code == 200
        assert 'access_token' in response.json().keys()
        self.jwt['user'] = response.json()['access_token']
        response = client.post('/user/login', json=self.new_admin)
        self.jwt['admin'] = response.json()['access_token']

    def test_login_user_invalid_nickname(self):
        response = client.post('/user/login', json={'nickname': 'invalid', 'password': 'pass'})
        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid username'}

    def test_login_user_invalid_password(self):
        response = client.post('/user/login', json={'nickname': 'nick', 'password': 'invalid'})
        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid password'}

    def test_user_profile(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get('/user', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {
            'id': response['id'],
            'nickname': self.new_user['nickname'],
            'is_active': True,
            'favorites': [],
            'number_my_recipe': 0
        }
        TestRoutes.user_id = response['id']

    def test_create_recipe(self):
        headers = {'jwt': self.jwt['user']}
        json = {'recipe_data': self.new_recipe, 'tags': ['tags1', 'tags2']}
        response = client.post('/recipe', json=json, headers=headers)
        assert response.status_code == 201
        response = response.json()
        assert list(response.keys()) == ['name', 'description', 'steps_making', 'type', 'is_active', 'date_creation',
                                         'id', 'photo', 'author', 'likes', 'tags']
        TestRoutes.recipe_id = int(response['id'])

    def test_create_recipe_invalid_type(self):
        headers = {'jwt': self.jwt['user']}
        invalid_recipe = self.new_recipe.copy()
        invalid_recipe['name'] = 'Invalid'
        invalid_recipe['type'] = 'invalid'
        json = {'recipe_data': invalid_recipe, 'tags': ['tags1', 'tags2']}
        response = client.post('/recipe', json=json, headers=headers)
        print(response.json())
        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid recipe type'}

    def test_add_photo(self):
        headers = {'jwt': self.jwt['user']}
        with open(basedir + r'/photo.jpg', 'rb') as f:
            file_data = f.read()
        file = {'photo': ('photo.jpg', file_data)}
        print(self.recipe_id)
        response = client.post(f'/recipe/{self.recipe_id}', json={}, files=file, headers=headers)
        print(response.json())
        assert response.status_code == 201
        assert response.json()['photo'] is not None

    def test_get_recipes(self):
        headers = {'jwt': self.jwt['user']}
        recipe = self.new_recipe.copy()
        recipe['name'] = 'Recipe 2'
        recipe['type'] = 'second'
        json = {'recipe_data': recipe, 'tags': ['tags1', 'tags3']}
        client.post('/recipe', json=json, headers=headers)
        recipe['name'] = 'Vodka'
        recipe['type'] = 'drink'
        json = {'recipe_data': recipe, 'tags': ['tags4']}
        client.post('/recipe', json=json, headers=headers)
        response = client.get(f'/recipe', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response) == 3

    def test_get_recipe_by_name(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f'/recipe?name=recipe', headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_recipe_by_type(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f'/recipe?type=drink', headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_recipe_by_tag(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f'/recipe?tag=tags1', headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_recipe_by_name_type(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f'/recipe?name=recipe&type=second', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response) == 1
        assert response[0]['name'] == 'Recipe 2'

    def test_get_recipe_by_name_tag(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f'/recipe?name=recipe&tag=tags3', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response) == 1
        assert response[0]['name'] == 'Recipe 2'

    def test_get_recipe_by_type_tag(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f'/recipe?type=drink&tag=tags4', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response) == 1
        assert response[0]['name'] == 'Vodka'

    def test_get_recipe_by_name_type_tag(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f'/recipe?name=recipe&type=dessert&tag=tags1', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response) == 1
        assert response[0]['name'] == 'Recipe'

    def test_like_it(self):
        headers = {'jwt': self.jwt['user']}
        response = client.post(f'/recipe/{self.recipe_id}/like', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {'user_id': response['user_id'], 'favorites': [int(self.recipe_id)]}

    def test_like_it_invalid_recipe_id(self):
        headers = {'jwt': self.jwt['user']}
        response = client.post(f'/recipe/{self.recipe_id-100}/like', headers=headers)
        print(response.json())
        assert response.status_code == 400
        assert response.json() == {'detail': 'There is no such recipe'}
        response = client.post(f'/recipe/asd/like', headers=headers)
        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid recipe_id must be a number'}

    def test_get_top_recipes(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get('/recipe/top?limit=5', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response[0]['id'] == self.recipe_id

    def test_get_favorites_recipe(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get('/recipe/like', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response[0]['id'] == self.recipe_id

    def test_get_my_recipe(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get('/recipe/my', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response) == 3

    def test_change_my_recipe(self):
        headers = {'jwt': self.jwt['user']}
        json = {"name": 'New Name', "description": 'New Description', "type": 'drink',
                "steps_making": '1. 2. 3.'}
        print(schemas.RecipeChange(**json))
        response = client.put(f'/recipe/{self.recipe_id}', json=json, headers=headers)
        print(response.json())
        assert response.status_code == 200

    def test_ban_recipe(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.put(f'/recipe/{self.recipe_id}/ban', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response['is_active'] is False

    def test_unban_recipe(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.put(f'/recipe/{self.recipe_id}/ban', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response['is_active'] is True

    def test_ban_user(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.put(f'/user/{self.user_id}/ban', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response['is_active'] is False

    def test_user_ban_create_recipe(self):
        headers = {'jwt': self.jwt['user']}
        json = {'recipe_data': self.new_recipe, 'tags': ['tags1', 'tags2']}
        response = client.post('/recipe', json=json, headers=headers)
        assert response.status_code == 405
        assert response.json() == {'detail': 'You don`t have permission to create a recipe'}

    def test_unban_user(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.put(f'/user/{self.user_id}/ban', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response['is_active'] is True

    def test_delete_recipe(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.delete(f'/recipe/{self.recipe_id}', headers=headers)
        assert response.status_code == 200
        assert response.json() == {'detail': f'The recipe ({self.recipe_id}) was deleted'}

    def test_delete_user(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.delete(f'/user/{self.user_id}', headers=headers)
        assert response.status_code == 200
        assert response.json() == {'detail': f'The user ({self.user_id}) was deleted'}


if __name__ == '__main__':
    unittest.main()
