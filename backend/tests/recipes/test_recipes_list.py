from http import HTTPStatus
from collections import OrderedDict

from django.db.models import Case, When
from django.conf import settings
from rest_framework.test import (APIClient, APITestCase,
                                 APIRequestFactory, force_authenticate)
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
        cls.tag = TagFactory()
        RecipeWithIngredientAmountFactory.create_batch(
            size=7,
            tags=(cls.tag,),
            shopping_cart_adds=(UserFactory(), cls.user),
            adds_to_favorites=(UserFactory(), cls.user),
        )
        cls.url = RECIPES_LIST_URL
        cls.recipes = Recipe.objects.all()
        cls.factory = APIRequestFactory()
        cls.view = RecipeViewset.as_view({'get': 'list'})

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(__class__.user)

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
        request = __class__.factory.get(__class__.url)
        force_authenticate(request, user=__class__.user)
        response = __class__.view(request)

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
        print(response.data)
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data.get('results'), expected_response)
        self.assertEqual(response.data.get('count'), len(all_recipes))

    def test_recipes_list_has_correct_fields(self):
        request = __class__.factory.get(__class__.url)
        force_authenticate(request, user=__class__.user)
        response = __class__.view(request)

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

    def test_recipes_list_filter_by_is_favorited(self):
        request_params = {'is_favorited': False}
        request = __class__.factory.get(__class__.url, data=request_params)
        force_authenticate(request, user=__class__.user)

        response = __class__.view(request)

        expected_response = []
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data.get('results'), expected_response)
        self.assertEqual(response.data.get('count'), 0)

    def test_recipes_list_filter_by_is_in_shopping_cart(self):
        request_params = {'is_in_shopping_cart': False}
        request = __class__.factory.get(__class__.url, data=request_params)
        force_authenticate(request, user=__class__.user)

        response = __class__.view(request)

        expected_response = []
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data.get('results'), expected_response)
        self.assertEqual(response.data.get('count'), 0)

    def test_recipes_list_filter_by_tags(self):
        another_tag = TagFactory()
        request_params = [
            {'tags': another_tag.slug},
            {'tags': __class__.tag.slug},
        ]
        for data in request_params:
            with self.subTest(data=data):
                request = __class__.factory.get(__class__.url, data=data)
                force_authenticate(request, user=__class__.user)
                response = __class__.view(request)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK
                )
                tagged_recipies_count = Recipe.objects.filter(
                    tags__slug=data['tags']
                ).count()
                self.assertEqual(
                    response.data.get('count'), tagged_recipies_count
                )

    def test_recipes_list_filter_by_author(self):
        another_user = UserFactory()
        request_params = [
            {'author': __class__.user.pk},
            {'author': another_user.pk},
        ]
        for data in request_params:
            with self.subTest(data=data):
                request = __class__.factory.get(__class__.url, data=data)
                force_authenticate(request, user=__class__.user)
                response = __class__.view(request)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK
                )
                tagged_recipies_count = Recipe.objects.filter(
                    author=data['author']
                ).count()
                self.assertEqual(
                    response.data.get('count'), tagged_recipies_count
                )
