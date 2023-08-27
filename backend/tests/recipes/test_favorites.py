from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase
from recipes.models import IngredientUnit

from tests.factories import UserFactory, RecipeFactory
from api.serializers import IngredientUnitSerializer

"""
class FavoritesTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.recipe = RecipeFactory()
        cls.url = f'/api/recipes/{cls.recipe.pk}/favorites/'

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_login(__class__.user)

    def test_add_to_favorites_unauthorised_correct(self):
        response = self.unauthorised_user.post(__class__.url)

        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED
        )
"""