from http import HTTPStatus
from collections import OrderedDict

from django.db.models import Case, When
from django.conf import settings
from rest_framework.test import APIClient, APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils.serializer_helpers import ReturnList

from api.views import RecipeViewset
from recipes.models import Recipe
from tests.factories import (UserFactory, TagFactory,
                             RecipeWithIngredientAmountFactory)
from api.serializers import RecipeListDetailSerializer

RECIPES_LIST_URL = '/api/recipes/'
PAGE_LIMIT = settings.REST_FRAMEWORK['PAGE_SIZE']


class RecipesListTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        RecipeWithIngredientAmountFactory.create_batch(
            size=7,
            tags=(TagFactory(), TagFactory()),
            shopping_cart_adds=(UserFactory(), UserFactory(), cls.user),
            adds_to_favorites=(UserFactory(), UserFactory(), cls.user),
        )
        cls.url = RECIPES_LIST_URL
        cls.recipes = Recipe.objects.all()
        cls.factory = APIRequestFactory()
        cls.view = RecipeViewset.as_view({'get': 'list'})

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_login(__class__.user)

        self.request = __class__.factory.get(__class__.url)
        force_authenticate(self.request, user=__class__.user)

    def test_recipes_list_unauthorised_ok(self):
        response = self.unauthorised_user.get(__class__.url)
        anonymous_user_favorites = []
        anonymous_user_shopping_cart = []
        all_recipes = __class__.recipes.annotate(
            is_favorited=Case(
                When(
                    id__in=anonymous_user_favorites,
                    then=True,
                ),
                default=False,
            )
        ).annotate(
            is_in_shopping_cart=Case(
                When(
                    id__in=anonymous_user_shopping_cart,
                    then=True,
                ),
                default=False,
            )
        )

        expected_response = RecipeListDetailSerializer(
            all_recipes[:PAGE_LIMIT],
            many=True,
        ).data
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data.get('results'), expected_response)
        self.assertEqual(response.data.get('count'), len(all_recipes))

    def test_recipes_list_authorised_ok(self):
        response = __class__.view(self.request)

        user_favorites = __class__.user.favorites.all()
        user_shopping_cart = __class__.user.shopping_cart.all()
        all_recipes = __class__.recipes.annotate(
            is_favorited=Case(
                When(
                    id__in=user_favorites,
                    then=True,
                ),
                default=False,
            )
        ).annotate(
            is_in_shopping_cart=Case(
                When(
                    id__in=user_shopping_cart,
                    then=True,
                ),
                default=False,
            )
        )
        expected_response = RecipeListDetailSerializer(
            all_recipes[:PAGE_LIMIT],
            many=True,
        ).data
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data.get('results'), expected_response)
        self.assertEqual(response.data.get('count'), len(all_recipes))

    def test_recipes_list_has_correct_fields(self):
        response = __class__.view(self.request)
        results_value = response.data.get('results')

        self.assertTrue(results_value)
        self.assertIsInstance(results_value, ReturnList)

        recipe = results_value[0]

        recipe_fields = set(recipe.keys())
        expected_recipe_fields = {
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        }
        self.assertEqual(
            recipe_fields,
            expected_recipe_fields,
        )

        recipe_author = recipe['author']
        self.assertIsInstance(recipe_author, OrderedDict)

        author_fields = set(recipe_author.keys())
        expected_author_fields = {
            'id',
            'first_name',
            'last_name',
            'email',
            'username',
            'is_subscribed',

        }
        self.assertEqual(
            author_fields,
            expected_author_fields,
        )
        recipe_tags = recipe['tags']
        self.assertIsInstance(recipe_tags, list)

        tags_fields = set(recipe_tags[0].keys())
        expected_tags_fields = {
            'id',
            'name',
            'color',
            'slug'
        }
        self.assertEqual(
            tags_fields,
            expected_tags_fields,
        )
        recipe_ingredients = recipe['ingredients']
        self.assertIsInstance(recipe_ingredients, list)

        ingredients_fields = set(recipe_ingredients[0].keys())
        expected_ingredients_fields = {
            'id',
            'name',
            'measurement_unit',
            'amount',
        }
        self.assertEqual(
            ingredients_fields,
            expected_ingredients_fields,
        )


"""
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "color": "#E26C2D",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Пупкин",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}


    def test_recipes_list_authorised_correct(self):
        response = self.authorised_user.get(__class__.url)

        expected_response = RecipeSerializer(
            __class__.ingredients, many=True
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)



    def test_recipes_list_correct_field_names(self):
        response = self.authorised_user.get(__class__.url)
        first_recipe_obj = list(response.data[0].keys())
        expected_fields = ['id', 'name', 'measurement_unit']
        self.assertEqual(
            first_ingredient_obj, expected_fields
        )

    def test_ingredient_create_not_allowed(self):
        url = IngredientsListTestCase.url
        data = {
            'name': "fish",
            'measurement_unit': 'g'
        }
        response = self.authorised_user.put(url, data=data)
        self.assertEqual(
            response.status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )
RecipeFactory.create_batch(
            size=5,
            tags=(TagFactory(), TagFactory()),
            ingredients=(IngredientUnit(), IngredientUnit())
        )
"""