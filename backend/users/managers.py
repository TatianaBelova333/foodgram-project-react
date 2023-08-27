from django.contrib.auth.models import BaseUserManager
from django.db import models


class UserRoles(models.TextChoices):
    USER = "user", 'Пользователь'
    ADMIN = "admin", 'Администратор'


class UserManager(BaseUserManager):
    """
    User model manager where email is the unique identifier
    for authentication instead of username.
    """
    def create_user(self, email, username, first_name,
                    last_name, role=UserRoles.USER, password=None):
        """
        Creates and saves a User with the given email and password
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )
        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, first_name='admin',
                         last_name='admin', password=None):
        """
        Creates and saves a superuser with the given email and password
        """
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            role=UserRoles.ADMIN,
        )

        user.save(using=self._db)
        return user
