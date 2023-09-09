import re
from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase
from recipes.models import Tag

from tests.factories import TagFactory, UserFactory
from api.serializers import TagSerializer


class TagDetailTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.tag = TagFactory()
        cls.url = f'/api/tags/{cls.tag.pk}/'

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(TagDetailTestCase.user)

    def test_tag_detail_unauthorised_correct(self):
        url = TagDetailTestCase.url
        response = self.unauthorised_user.get(url)

        expected_response = TagSerializer(
            TagDetailTestCase.tag,
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_tag_detail_authorised_correct(self):
        url = TagDetailTestCase.url
        response = self.authorised_user.get(url)

        expected_response = TagSerializer(
            TagDetailTestCase.tag,
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_tag_detail_correct_field_names(self):
        url = TagDetailTestCase.url
        response = self.authorised_user.get(url)
        first_tag_obj = set(response.data.keys())
        expected_fields = {'id', 'name', 'color', 'slug'}
        self.assertEqual(
            first_tag_obj, expected_fields
        )

    def test_tag_detail_hex_color_value(self):
        url = TagDetailTestCase.url
        response = self.authorised_user.get(url)
        first_tag_obj_color = response.data['color']
        regex = r"^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$"
        self.assertTrue(
            re.fullmatch(regex, first_tag_obj_color),
        )

    def test_tag_detail_404(self):
        tag = TagFactory()
        Tag.objects.filter(pk=tag.pk).delete()
        url = f'/api/tags/{tag.pk}/'
        response = self.authorised_user.get(url)

        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND
        )

    def test_tag_detail_patch(self):
        url = TagDetailTestCase.url
        data = {
            'color': 'FF5733',
            'slug': 'brunch',
            'name': 'бранч'
        }
        response = self.authorised_user.patch(
            url,
            data=data,
            content_type='application/json',
        )
        self.assertEqual(
            response.status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )

    def test_tag_detail_delete(self):
        url = TagDetailTestCase.url

        response = self.authorised_user.delete(url)
        self.assertEqual(
            response.status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )
