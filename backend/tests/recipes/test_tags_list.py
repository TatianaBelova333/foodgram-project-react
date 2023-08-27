import re
from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase
from recipes.models import Tag

from tests.factories import TagFactory, UserFactory
from api.serializers import TagSerializer

TAGS_LIST_URL = '/api/tags/'


class TagsListTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        TagFactory.create_batch(size=3)
        cls.user = UserFactory()
        cls.tags = Tag.objects.all()
        cls.url = TAGS_LIST_URL

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_login(TagsListTestCase.user)

    def test_tags_list_unauthorised_correct(self):
        response = self.unauthorised_user.get(__class__.url)

        expected_response = TagSerializer(
            __class__.tags, many=True
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_tags_list_authorised_correct(self):
        response = self.authorised_user.get(__class__.url)

        expected_response = TagSerializer(
            __class__.tags, many=True
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_tags_list_correct_field_names(self):
        response = self.authorised_user.get(__class__.url)
        first_tag_obj = set(response.data[0].keys())
        expected_fields = {'id', 'name', 'color', 'slug'}
        self.assertEqual(
            first_tag_obj, expected_fields
        )

    def test_tags_list_hex_color_value(self):
        response = self.authorised_user.get(__class__.url)
        first_tag_obj_color = response.data[0]['color']
        regex = r"^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$"
        self.assertTrue(
            re.fullmatch(regex, first_tag_obj_color),
        )
