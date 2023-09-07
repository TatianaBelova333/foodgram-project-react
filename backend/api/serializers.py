import base64
from collections import Counter
from typing import OrderedDict

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import DatabaseError, transaction
from djoser.serializers import (
    SetPasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from rest_framework import serializers

from recipes.models import IngredientUnit, Recipe, RecipeIngredientAmount, Tag
from users.models import Subscription

User = get_user_model()


class CustomSetPasswordSerializer(SetPasswordSerializer):
    """Validate that the current and new password values are different."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        current_password = attrs['current_password']
        new_password = attrs['new_password']
        if current_password == new_password:
            raise serializers.ValidationError(
                {"new_password": ("Новый пароль должен отличаться "
                                  "от текущего пароля.")}
            )
        return attrs


class UserRegistrationSerializer(UserCreateSerializer):
    """
    Serializer for registering new users.

    """

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'id',
        ]
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Hash the new user's password before saving."""
        first_name = validated_data.pop('first_name').capitalize()
        last_name = validated_data.pop('last_name').capitalize()

        user = User.objects.create(first_name=first_name,
                                   last_name=last_name,
                                   **validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomUserSerializer(UserSerializer):
    """
    Serialiser for registered users' profiles.

    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'username',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            request_user = request.user
            other_user = obj.id
            return (request_user.is_authenticated
                    and Subscription.objects.filter(
                        user=request_user,
                        author=other_user
                    ).exists())
        return False


class CurrentUserSerializer(CustomUserSerializer):
    """
    Serializer for the current request user profile.

    """

    def get_is_subscribed(self, obj):
        """
        Always return False as the current user
        cannot be subscribed to their own accounts.

        """
        return False


class IngredientUnitSerializer(serializers.ModelSerializer):
    """Ingredient model serializer."""
    measurement_unit = serializers.StringRelatedField(read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)

    class Meta:
        model = IngredientUnit
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Serializer for recipe tags."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientUnitAmountSerializer(serializers.ModelSerializer):
    """Ingredient model serializer."""
    id = serializers.IntegerField(source='ingredient_unit.id')
    name = serializers.CharField(
        source='ingredient_unit.ingredient.name',
        read_only=True,
    )
    measurement_unit = serializers.CharField(
        source='ingredient_unit.measurement_unit.name',
        read_only=True,
    )

    class Meta:
        model = RecipeIngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if value < 1 or value > 2000:
            raise serializers.ValidationError(
                'Количество должно быть не менее 1 '
                'и не более 2000 единиц.'
            )
        return value


class RecipeListDetailSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True, allow_null=False)
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer()
    ingredients = IngredientUnitAmountSerializer(
        many=True,
        source='recipeingredientamount_set',
    )
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'name',
            'text',
            'image',
            'cooking_time',
            'text',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        ]


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(
        default=serializers.CurrentUserDefault(),
        read_only=True,
    )
    ingredients = IngredientUnitAmountSerializer(
        many=True,
        source='recipeingredientamount_set',
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'tags',
            'ingredients',
            'cooking_time',
            'text',
            'image',
            'author',
        ]
        read_only_fields = ('id',)

    #  вернула проверку наличия в базе ингредиентов,
    #  т.к.сериализатор в этом не помог
    def validate_ingredients(self, ingredients):
        """Validate that ingredients field is not empty, and
        contains valid ingredient_unit ids."""
        if len(ingredients) == 0:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.'
            )

        for ingredient in ingredients:
            ingr_unit_id = ingredient['ingredient_unit']['id']
            if not IngredientUnit.objects.filter(
                pk=ingr_unit_id
            ).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id '
                    f'{ingr_unit_id} '
                    f' не существует'
                )
        return ingredients

    # пришлось убрать валидацию дубликатов игредиентов сюда,
    # т.к. не показывает фронтенд ен показывает
    # сообщение об ошибке пользовталю из validate_ingredients
    def validate(self, data):
        """Validate that ingredients are unique."""
        ingredients = data['recipeingredientamount_set']
        ingr_count = Counter(
            ingr['ingredient_unit']['id'] for ingr in ingredients
        )
        ingr_duplicates_exist = ingr_count.total() != len(ingr_count)
        if ingr_duplicates_exist:
            raise serializers.ValidationError(
                'Некоторые ингредиенты дублируются.'
            )
        return data

    def __add_ingredients(
            self,
            recipe: Recipe,
            ingredients: list[OrderedDict]
    ) -> None:
        for ingredient in ingredients:
            ingr_unit_id = ingredient['ingredient_unit']['id']
            ingr_unit = IngredientUnit.objects.get(
                pk=ingr_unit_id,
            )
            RecipeIngredientAmount.objects.create(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient_unit=ingr_unit,
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('recipeingredientamount_set')
        tags = validated_data.pop('tags')
        try:
            with transaction.atomic():
                recipe = Recipe.objects.create(**validated_data)
                self.__add_ingredients(recipe, ingredients)
                recipe.tags.add(*tags)
                recipe.save()
        except DatabaseError:
            raise serializers.ValidationError('Не удалось создать рецепт.')

        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredientamount_set')
        try:
            with transaction.atomic():
                recipe.tags.clear()
                recipe.tags.add(*tags)

                recipe.ingredients.clear()
                self.__add_ingredients(recipe, ingredients)
                recipe.save()
        except DatabaseError:
            raise serializers.ValidationError(
                f'Не удалось отредактировать рецепт - {recipe.name}.'
            )

        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags,
            many=True,
        ).data
        return representation


class RecipeBriefInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time',
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for users' subcriptions."""
    id = serializers.IntegerField(source='author.pk')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    email = serializers.CharField(source='author.email')
    recipes = RecipeBriefInfoSerializer(
        many=True, read_only=True, source='author.recipes'
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'recipes',
            'is_subscribed',
            'recipes_count',
        ]

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()
