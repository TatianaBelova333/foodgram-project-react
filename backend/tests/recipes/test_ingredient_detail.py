from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase
from recipes.models import IngredientUnit

from tests.factories import IngredientUnitFactory, UserFactory
from api.serializers import IngredientUnitSerializer


class IngredientDetailTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.ingredient = IngredientUnitFactory()
        cls.url = f'/api/ingredients/{cls.ingredient.pk}/'

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_login(__class__.user)

    def test_ingredient_detail_unauthorised_correct(self):
        response = self.unauthorised_user.get(__class__.url)

        expected_response = IngredientUnitSerializer(
            __class__.ingredient,
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_ingredient_detail_authorised_correct(self):
        response = self.authorised_user.get(__class__.url)

        expected_response = IngredientUnitSerializer(
            __class__.ingredient,
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_ingredientdetail_correct_field_names(self):
        response = self.authorised_user.get(__class__.url)
        ingredient_fields = set(response.data.keys())
        expected_fields = {'id', 'name', 'measurement_unit'}
        self.assertEqual(
            ingredient_fields, expected_fields
        )

    def test_ingredient_detail_404(self):
        ingredient = IngredientUnitFactory()
        IngredientUnit.objects.filter(pk=ingredient.pk).delete()
        url = f'/api/ingredients/{ingredient.pk}/'
        response = self.authorised_user.get(url)

        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND
        )

    def test_ingredient_detail_patch(self):
        data = {
            'measurement_unit': 'kg',
            'name': 'potato',
        }
        response = self.authorised_user.patch(
            __class__.url,
            data=data,
            content_type='application/json',
        )
        self.assertEqual(
            response.status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )

    def test_ingredient_detail_delete(self):
        response = self.authorised_user.delete(__class__.url)
        self.assertEqual(
            response.status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )
