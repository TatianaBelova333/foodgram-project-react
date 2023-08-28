from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model


from tests.factories import UserFactory
from api.serializers import CurrentUserSerializer


User = get_user_model()


class CurrentUserDetailTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.current_user = UserFactory()
        cls.another_user = UserFactory()
        cls.url = '/api/users/me/'

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(__class__.current_user)

    def test_current_user_detail_unauthorised_correct(self):
        response = self.unauthorised_user.get(__class__.url)
        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED
        )

    def test_current_user_detail_authorised_correct(self):
        response = self.authorised_user.get(__class__.url)
        user_pk = response.data.get('id')
        expected_user_pk = __class__.current_user.pk
        expected_response = CurrentUserSerializer(
            __class__.current_user,
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)
        self.assertEqual(user_pk, expected_user_pk)

    def test_current_user_detail_has_correct_fields(self):
        response = self.authorised_user.get(__class__.url)
        single_user_fields = set(response.data.keys())
        expected_user_fields = {
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        }
        self.assertEqual(single_user_fields, expected_user_fields)

    def test_current_user_patch_forbidden(self):
        response = self.authorised_user.patch(
            __class__.url, data={'last_name': 'Katya'}
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_current_user_delete_forbidden(self):
        response = self.authorised_user.delete(__class__.url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
