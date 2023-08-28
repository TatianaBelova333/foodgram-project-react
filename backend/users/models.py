from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.core.exceptions import ValidationError

from users.managers import UserRoles, UserManager


class User(AbstractUser):
    """Custom User model."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    username = models.CharField(
        'Юзернейм',
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and '
        '@/./+/-/_ only.',
        validators=[
            RegexValidator(r'^[\w.@+-]+$',
                           'Enter a valid username. '
                           'This value may contain only letters, numbers '
                           'and @/./+/-/_ characters.'),
        ],
        error_messages={
            'unique': "Данный логин уже занят другим пользователем.",
        })
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    email = models.EmailField('Почтовый ящик', unique=True, max_length=254)
    password = models.CharField('Пароль', max_length=150)
    role = models.CharField(
        max_length=5,
        choices=UserRoles.choices,
        default=UserRoles.USER,
    )

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return self.role == UserRoles.ADMIN

    @property
    def is_user(self):
        return self.role == UserRoles.USER

    @property
    def is_superuser(self):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.

        """
        full_name = (f'{self.first_name.capitalize()} '
                     f'{self.last_name.capitalize()}')
        return full_name.strip()

    def __str__(self):
        return self.username

    def added_recipes_count(self):
        return self.recipes.count()

    added_recipes_count.short_description = 'Кол-во добавленных рецептов'


class Subscription(models.Model):
    """Model for user subscriptions."""
    is_cleaned = False

    user = models.ForeignKey(
        User,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='user_author'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'

    def clean(self):
        """
        Raise ValidatioError if the user and the author are
        the same User instance.

        """
        self.is_cleaned = True
        if self.user == self.author:
            raise ValidationError(
                'Пользователь не может подписаться на самого себя'
            )
        super(Subscription, self).clean()

    def save(self, *args, **kwargs):
        """
        Does not save a Subscription instance if the user and
        the recipe author are the same User instance.

        """
        if not self.is_cleaned:
            self.full_clean()
        super(Subscription, self).save(*args, **kwargs)
