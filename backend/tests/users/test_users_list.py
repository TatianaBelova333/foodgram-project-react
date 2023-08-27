from http import HTTPStatus
from django.conf import settings

from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model

from tests.factories import UserFactory
from api.serializers import CustomUserSerializer

USERS_LIST_URL = '/api/users/'

User = get_user_model()

PAGE_LIMIT = settings.REST_FRAMEWORK['PAGE_SIZE']


class UserListTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        UserFactory.create_batch(size=(PAGE_LIMIT + 1))
        cls.user = UserFactory()
        cls.url = USERS_LIST_URL
        cls.users = User.objects.all()

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_login(__class__.user)

    def test_users_list_unauthorised_correct(self):
        response = self.unauthorised_user.get(__class__.url)

        expected_response = CustomUserSerializer(
            __class__.users[:PAGE_LIMIT], many=True
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data.get('results'), expected_response)

    def test_users_list_authorised_correct(self):
        response = self.authorised_user.get(__class__.url)
        all_users = __class__.users

        expected_response = CustomUserSerializer(
            all_users[:PAGE_LIMIT], many=True
        ).data
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data.get('results'), expected_response)
        self.assertEqual(response.data.get('count'), len(all_users))

    def test_users_list_has_correct_fields(self):
        response = self.authorised_user.get(__class__.url)
        first_user = response.data['results'][0]
        first_user_fields = set(first_user.keys())
        expected_user_fields = {
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        }
        self.assertEqual(first_user_fields, expected_user_fields)
