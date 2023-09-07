from http import HTTPStatus

from rest_framework.test import (APIClient, APITestCase)
from rest_framework.exceptions import ErrorDetail
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from tests.factories import UserFactory


User = get_user_model()


class UserSetPasswordTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = '/api/users/set_password/'
        cls.user = UserFactory(
            username='test', email='test@mail.ru')

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(__class__.user)

    def test_user_set_password_authorised_ok(self):
        current_password = 'OLD_Dyskig-fubnas-dozby1'
        __class__.user.set_password(current_password)
        payload = {
            "current_password": current_password,
            "new_password": "Dyskig-fubnas-dozby1NEW",
        }
        response = self.authorised_user.post(
            __class__.url,
            data=payload,
        )
        self.assertEqual(
            response.status_code, HTTPStatus.NO_CONTENT
        )
        self.assertTrue(
            check_password(payload['new_password'],
                           __class__.user.password)
        )

    def test_user_set_password_unauthorised(self):
        payload = {
            "current_password": "Dyskig-fubnas-dozby1OLD",
            "new_password": "Dyskig-fubnas-dozby1NEW",
        }
        response = self.unauthorised_user.post(
            __class__.url,
            data=payload,
        )
        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED
        )

    def test_user_set_password_missing_fields(self):
        current_password = 'OLD_Dyskig-fubnas-dozby1'
        __class__.user.set_password(current_password)

        data = {
            "current_password": current_password,
            "new_password": "Dyskig-fubnas-dozby1NEW",
        }
        missing_fields = ["current_password", "new_password"]
        for missing_field in missing_fields:
            with self.subTest(missing_field=missing_field):
                payload = data.copy()
                del payload[missing_field]
                response = self.authorised_user.post(
                    __class__.url,
                    data=payload,
                )
                self.assertEqual(
                    response.data[missing_field][0].code,
                    'required',
                )

    def test_user_set_password_wrong_current_password(self):
        current_password = 'OLD_Dyskig-fubnas-dozby1'
        __class__.user.set_password(current_password)

        payload = {
            "current_password": current_password + 'test',
            "new_password": "Dyskig-fubnas-dozby1NEW",
        }
        response = self.authorised_user.post(
            __class__.url,
            data=payload,
        )
        self.assertEqual(
            response.status_code, HTTPStatus.BAD_REQUEST
        )
        self.assertEqual(
            response.data['current_password'][0].code,
            'invalid_password',
        )

    def test_user_set_password_to_same_password_400(self):
        current_password = 'OLD_Dyskig-fubnas-dozby1'
        __class__.user.set_password(current_password)

        payload = {
            "current_password": current_password,
            "new_password": current_password,
        }
        response = self.authorised_user.post(
            __class__.url,
            data=payload,
        )
        expected_response = {'new_password': [ErrorDetail(
            string=('Новый пароль должен отличаться '
                    'от текущего пароля.'),
            code='invalid',
        )]}
        self.assertEqual(
            response.status_code, HTTPStatus.BAD_REQUEST
        )
        self.assertEqual(
            response.data, expected_response
        )
