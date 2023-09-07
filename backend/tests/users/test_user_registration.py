from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase
from rest_framework.exceptions import ErrorDetail
from django.contrib.auth import get_user_model
from django.utils import timezone

from tests.factories import UserFactory


User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = '/api/users/'
        UserFactory(username='test', email='test@mail.ru')

    def setUp(self):
        self.unauthorised_user = APIClient()

    def test_user_registration_ok(self):
        start_time = timezone.now()
        payload = {
            "email": "vpupkin@yandex.ru",
            "username": "vasya.pupkin",
            "first_name": "Вася",
            "last_name": "Пупкин",
            "password": "Qwerty123fgfgrt"
        }
        response = self.unauthorised_user.post(
            __class__.url,
            data=payload,
        )

        newly_registered_user = User.objects.last()
        expected_response = {
            "email": "vpupkin@yandex.ru",
            "id": newly_registered_user.pk,
            "username": "vasya.pupkin",
            "first_name": "Вася",
            "last_name": "Пупкин"
        }
        self.assertEqual(
            response.status_code, HTTPStatus.CREATED
        )
        self.assertTrue(User.objects.filter(
            email=payload['email'],
            username=payload['username'],
            first_name=payload['first_name'],
            last_name=payload['last_name'],
            date_joined__range=(start_time, timezone.now()),
        ).exists())
        self.assertEqual(response.data, expected_response)

    def test_user_registration_unique_fields(self):
        start_time = timezone.now()
        payload = {
            "email": "test@mail.ru",
            "username": "test",
            "first_name": "Вася",
            "last_name": "Пупкин",
            "password": "Qwerty123fgfgrt"
        }
        response = self.unauthorised_user.post(
            __class__.url,
            data=payload,
        )
        expected_response = {
            'username': [ErrorDetail(
                string='Данный логин уже занят другим пользователем.',
                code='unique'
            )],
            'email': [ErrorDetail(
                string='Пользователь с таким Почтовый ящик уже существует.',
                code='unique')]
        }
        self.assertEqual(
            response.status_code, HTTPStatus.BAD_REQUEST,
        )
        self.assertFalse(User.objects.filter(
            email=payload['email'],
            username=payload['username'],
            first_name=payload['first_name'],
            last_name=payload['last_name'],
            date_joined__range=(start_time, timezone.now()),
        ).exists())
        self.assertEqual(response.data, expected_response)

    def test_user_registration_missing_required_fields(self):
        data = {
            "email": "test_email@mail.ru",
            "username": "test_username",
            "first_name": "Вася",
            "last_name": "Пупкин",
            "password": "Qwerty123fgfgrt"
        }
        missing_fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        ]
        for missing_field in missing_fields:
            with self.subTest(missing_field=missing_field):
                payload = data.copy()
                del payload[missing_field]
                response = self.unauthorised_user.post(
                    __class__.url,
                    data=payload,
                )
                print(response.data)
                self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
                self.assertEqual(
                    response.data[missing_field][0].code,
                    'required'
                )
