from http import HTTPStatus

from rest_framework.test import APIClient, APITestCase

from tests.factories import UserFactory, SubscriptionFactory
from users.models import Subscription


class UserSubscriptionsTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.another_user = UserFactory()
        cls.url = '/api/users/{user_pk}/subscribe/'.format

    def setUp(self):
        self.unauthorised_user = APIClient()

        self.authorised_user = APIClient()
        self.authorised_user.force_authenticate(__class__.user)

    def test_user_subscribe_post_by_unauthorised_user(self):
        response = self.unauthorised_user.post(
            __class__.url(user_pk=__class__.another_user.pk)
        )

        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED
        )

    def test_user_subscribe_delete_by_unauthorised_user(self):
        response = self.unauthorised_user.delete(
            __class__.url(user_pk=__class__.another_user.pk)
        )

        self.assertEqual(
            response.status_code, HTTPStatus.UNAUTHORIZED
        )

    def test_user_subscribe_post_by_authorised_user(self):
        response = self.authorised_user.post(
            __class__.url(user_pk=__class__.another_user.pk)
        )

        self.assertEqual(
            response.status_code, HTTPStatus.CREATED
        )
        self.assertTrue(Subscription.objects.filter(
            user=__class__.user,
            author=__class__.another_user
        ).exists())

    def test_user_subscribe_delete_by_authorised_user(self):
        some_author = UserFactory()
        SubscriptionFactory(
            user=__class__.user,
            author=some_author,
        )
        self.assertTrue(Subscription.objects.filter(
            user=__class__.user,
            author=some_author
        ).exists())

        response = self.authorised_user.delete(
            __class__.url(user_pk=some_author.pk))

        self.assertEqual(
            response.status_code, HTTPStatus.NO_CONTENT
        )
        self.assertFalse(Subscription.objects.filter(
            user=__class__.user,
            author=some_author
        ).exists())

    def test_user_subscribe_to_themselvres_400(self):
        request_user = __class__.user
        response = self.authorised_user.post(
            __class__.url(user_pk=request_user.pk))

        self.assertEqual(
            response.status_code,
            HTTPStatus.BAD_REQUEST
        )
        self.assertFalse(Subscription.objects.filter(
            user=request_user,
            author=request_user,
        ).exists())

    def test_user_subscribe_post_subscription_already_exists(self):
        some_author = UserFactory()
        SubscriptionFactory(
            user=__class__.user,
            author=some_author,
        )
        response = self.authorised_user.post(
            __class__.url(user_pk=some_author.pk))

        self.assertEqual(
            response.status_code, HTTPStatus.BAD_REQUEST
        )

    def test_user_subscribe_delete_subscription_already_exists(self):
        some_author = UserFactory()
        SubscriptionFactory(
            user=__class__.user,
            author=some_author,
        )
        Subscription.objects.filter(
            user=__class__.user,
            author=some_author,
        ).delete()
        response = self.authorised_user.delete(
            __class__.url(user_pk=some_author.pk))

        self.assertEqual(
            response.status_code, HTTPStatus.BAD_REQUEST
        )
