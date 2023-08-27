from http import HTTPStatus

from rest_framework.test import (APIClient, APITestCase,
                                 APIRequestFactory, force_authenticate)
from django.contrib.auth import get_user_model

from api.views import CustomUserViewSet
from users.managers import UserRoles
from users.models import Subscription
from tests.factories import UserFactory, SubscriptionFactory
from api.serializers import CustomUserSerializer


User = get_user_model()


class UserDetailTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.another_user = UserFactory()
        cls.url = f'/api/users/{cls.user.pk}/'

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(__class__.user)

        self.another_authorised_user = APIClient()
        self.another_authorised_user.force_authenticate(__class__.another_user)

    def test_user_detail_unauthorised_ok(self):
        response = self.unauthorised_user.get(__class__.url)
        expected_response = CustomUserSerializer(
            __class__.user,
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_user_detail_authorised_ok(self):
        response = self.authorised_user.get(__class__.url)
        expected_response = CustomUserSerializer(
            __class__.user,
        ).data

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)

    def test_user_detail_by_another_authorised_user_ok(self):
        response = self.another_authorised_user.get(__class__.url)
        detail_user_pk = response.data.get('id')
        expected_response = CustomUserSerializer(
            __class__.user,
        ).data

        expected_user_pk = __class__.user.pk

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(response.data, expected_response)
        self.assertEqual(detail_user_pk, expected_user_pk)

    def test_user_detail_has_correct_fields(self):
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

    def test_user_detail_is_subscribed_correct(self):
        factory = APIRequestFactory()
        view = CustomUserViewSet.as_view({'get': 'retrieve'})
        request = factory.get(__class__.url)
        request.user = __class__.user
        force_authenticate(request, user=request.user)

        SubscriptionFactory(user=request.user, author=__class__.another_user)

        first_response = view(request, id=self.another_user.pk)
        detail_user_is_subscribed_field = first_response.data.get(
            'is_subscribed',
        )
        self.assertTrue(detail_user_is_subscribed_field)

        Subscription.objects.filter(
            user=request.user, author=__class__.another_user
        ).delete()

        second_response = view(request, id=self.another_user.pk)
        detail_user_is_subscribed_field = second_response.data.get(
            'is_subscribed'
        )
        self.assertFalse(detail_user_is_subscribed_field)

    def test_detail_user_patch_forbidden(self):
        response = self.authorised_user.patch(
            __class__.url, data={'last_name': 'Katya'}
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_detail_user_patch_by_admin_forbidden(self):
        request_user = __class__.user
        request_user.role = UserRoles.ADMIN
        response = self.authorised_user.patch(
            __class__.url, data={'last_name': 'Katya'}
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
