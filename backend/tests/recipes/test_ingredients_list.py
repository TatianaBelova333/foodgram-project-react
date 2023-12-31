from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase

from recipes.models import IngredientUnit
from tests.factories import (IngredientUnitFactory, UserFactory,
                             IngredientFactory)
from api.serializers import IngredientUnitSerializer

INGREDIENTS_LIST_URL = '/api/ingredients/'


class IngredientsListTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        IngredientUnitFactory.create_batch(size=5)
        cls.user = UserFactory()
        cls.ingredients = IngredientUnit.objects.all()
        cls.url = INGREDIENTS_LIST_URL

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(IngredientsListTestCase.user)

    def test_ingredients_list_unauthorised_correct(self):
        response = self.unauthorised_user.get(__class__.url)

        expected_response = IngredientUnitSerializer(
            __class__.ingredients, many=True
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_ingredients_list_authorised_correct(self):
        response = self.authorised_user.get(__class__.url)

        expected_response = IngredientUnitSerializer(
            __class__.ingredients, many=True
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_ingredients_list_correct_field_names(self):
        response = self.authorised_user.get(__class__.url)
        first_ingredient_obj = set(response.data[0].keys())
        expected_fields = {'id', 'name', 'measurement_unit'}
        self.assertEqual(
            first_ingredient_obj, expected_fields
        )

    def test_ingredient_create_not_allowed(self):
        data = {
            'name': "fish",
            'measurement_unit': 'g'
        }
        response = self.authorised_user.put(__class__.url, data=data)
        self.assertEqual(
            response.status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )

    def test_ingredients_filter_by_name_case_insensitive(self):
        ingredient_for_search = IngredientFactory(name='капуста')
        IngredientUnitFactory(
            ingredient=ingredient_for_search,
        )
        params = [
            {'name': 'Кап'},
            {'name': 'пус'},
        ]
        for data in params:
            with self.subTest(data=data):
                response = self.authorised_user.get(__class__.url, data=data)
                searched_ingredient = IngredientUnit.objects.filter(
                    ingredient__name__icontains=data['name'],
                )
                expected_result = IngredientUnitSerializer(
                    searched_ingredient, many=True,
                ).data
                self.assertEqual(
                    response.status_code, HTTPStatus.OK
                )
                self.assertEqual(response.data, expected_result)
