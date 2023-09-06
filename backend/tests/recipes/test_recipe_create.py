from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.utils import timezone
from rest_framework.test import (APIClient, APITestCase,
                                 APIRequestFactory,
                                 force_authenticate)
from django.test import override_settings

from api.views import RecipeViewset
from recipes.models import Recipe
from tests.factories import (UserFactory, TagFactory,
                             IngredientUnitFactory,
                             IngredientFactory,
                             MeasurementUnitFactory
                             )

RECIPE_CREATE_URL = '/api/recipes/'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RecipeCreateTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.tag = TagFactory()
        cls.url = RECIPE_CREATE_URL
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

        self.factory = APIRequestFactory()
        self.view = RecipeViewset.as_view({'post': 'create'})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_recipe_create_unauthorised_ok(self):
        data = {
            "ingredients": [
                {
                    'id': self.ingredient_unit.id,
                    'amount': 10
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

        response = self.unauthorised_user.post(
            __class__.url,
            data=data,
        )

        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED,
        )

    def test_recipe_create_authorised_ok(self):
        start_time = timezone.now()
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
            "name": "Testcreate",
            "text": "TestCreate",
            "cooking_time": 1,
        }

        request = self.factory.post(self.url, data=data, format='json')
        request.user = __class__.user
        force_authenticate(request, user=request.user)

        response = self.view(request)

        self.assertEqual(
            response.status_code, HTTPStatus.CREATED,
        )
        self.assertTrue(
            Recipe.objects.filter(
                text=data['text'],
                name=data['name'],
                author=request.user,
                cooking_time=data['cooking_time'],
                tags__in=data['tags'],
                pub_date__range=(start_time, timezone.now()),
            ).exists()
        )

    def test_recipe_create_missing_required_fields(self):
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
            "name": "Testcreate",
            "text": "TestCreate",
            "cooking_time": 1,
        }
        missing_fields = [
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        ]
        for missing_field in missing_fields:
            with self.subTest(missing_field=missing_field):
                payload = data.copy()
                del payload[missing_field]

                request = self.factory.post(self.url, data=payload, format='json')
                request.user = __class__.user
                force_authenticate(request, user=request.user)

                response = self.view(request)

                self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
                self.assertEqual(
                    response.data[missing_field][0].code,
                    'required',
                )
