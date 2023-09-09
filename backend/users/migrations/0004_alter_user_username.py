# Generated by Django 4.2.4 on 2023-09-09 07:37

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(
                error_messages={
                    'unique': 'Данный логин уже занят другим пользователем.'
                },
                help_text='Обязательное поле. Не более 150 символов. Буквы, цифры и @/./+/-/_.',
                max_length=150,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        code='invalid_username',
                        message='Имя пользователя должно содержать только буквы, цифры и следующие символы: @/./+/-/_.',
                        regex='^[\\w.@+-]+$',
                    )
                ],
                verbose_name='Юзернейм',
            ),
        ),
    ]
