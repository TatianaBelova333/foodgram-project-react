from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase

from tests.factories import UserFactory, SubscriptionFactory

USERS_SUBSCRIPTIONS_URL = '/api/users/subscriptions/'


class UserSubscriptionsTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        SubscriptionFactory(user=cls.user, author=UserFactory())
        SubscriptionFactory(user=cls.user, author=UserFactory())
        cls.url = USERS_SUBSCRIPTIONS_URL

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(__class__.user)

    def test_users_subscriptions_by_unauthorised_401(self):
        response = self.unauthorised_user.get(__class__.url)

        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED
        )

    def test_users_subscriptions_by_authorised_user(self):
        response = self.authorised_user.get(__class__.url)
        print(response.data)
        expected_subscriptions_count = __class__.user.subscriptions.count()
        response_subscriptions_count = response.data.get('count', -1)

        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(
            expected_subscriptions_count,
            response_subscriptions_count,
        )
