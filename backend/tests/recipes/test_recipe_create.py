from http import HTTPStatus

from rest_framework.test import (APIClient, APITestCase,
                                 APIRequestFactory)

from api.views import RecipeViewset
from tests.factories import (UserFactory, TagFactory,
                             IngredientUnitFactory,
                             IngredientFactory,
                             MeasurementUnitFactory
                             )

RECIPE_CREATE_URL = '/api/recipes/'


class RecipesListTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.tag = TagFactory()
        cls.url = RECIPE_CREATE_URL
        cls.factory = APIRequestFactory()
        cls.view = RecipeViewset.as_view({'get': 'list'})
        cls.ingredient = IngredientFactory()
        cls.unit = MeasurementUnitFactory()
        cls.ingredient_unit = IngredientUnitFactory(
            ingredient=cls.ingredient,
            measurement_unit=cls.unit,
        )

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(__class__.user)

    def test_recipes_list_unauthorised_ok(self):
        data = {
            'ingredients': [
                {
                    'id': self.ingredient_unit.ingredient.pk,
                    'amount': 10
                }
            ],
            "tags": [
                self.tag.pk,
            ],
            'image': ("data:image/png;base64,iVBORw0KGgoAAAANSUh"
                      "EUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///"
                      "9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAC"
                      "klEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="),
            'name': "string",
            'text': "string",
            'cooking_time': 1,
        }

        response = self.unauthorised_user.post(
            __class__.url,
            data=data,
        )

        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED,
        )

"""
    def test_recipes_list_authorised_ok(self):
        data = {
            "ingredients": [
                {
                    "id": self.ingredient_unit.pk,
                    "amount": 10,
                }
            ],
            "tags": [
                self.tag.pk,
            ],
            "image": ("data:image/png;base64,iVBORw0KGgoAAAANSUh"
                      "EUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///"
                      "9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAC"
                      "klEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="),
            "name": "string",
            "text": "string",
            "cooking_time": 1,
        }
        factory = APIRequestFactory()
        view = RecipeViewset.as_view({'post': 'create'})
        request = factory.post(__class__.url, data=data)
        request.user = __class__.user
        force_authenticate(request, user=request.user)

        response = view(request)

        print(response.data)

        self.assertEqual(
            response.status_code, HTTPStatus.OK,
        )
"""
