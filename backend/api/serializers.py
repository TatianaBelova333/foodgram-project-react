import base64

from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import (UserCreateSerializer, UserSerializer,
                                SetPasswordSerializer)
from django.core.files.base import ContentFile

import webcolors

from recipes.models import IngredientUnit, Tag, Recipe, RecipeIngredientAmount
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


class Name2HexColor(serializers.Field):
    """Serializer for converting color names into valid hex-codes."""

    def to_representation(self, value):
        try:
            data = webcolors.name_to_hex(value.name)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет HEX-кода')
        return data


class TagSerializer(serializers.ModelSerializer):
    """Serializer for recipe tags."""
    color = Name2HexColor()

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
    id = serializers.IntegerField(source='ingredient_unit.pk')
    name = serializers.CharField(source='ingredient_unit.ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient_unit.measurement_unit.name'
    )

    class Meta:
        model = RecipeIngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientUnitAmountCreateSerializer(serializers.ModelSerializer):
    """Ingredient model serializer."""
    id = serializers.IntegerField(source='ingredient_unit.pk')

    class Meta:
        model = RecipeIngredientAmount
        fields = ('id', 'amount')


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
    ingredients = IngredientUnitAmountCreateSerializer(
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
        read_only_fields = ('id', )

    def validate(self, data):
        ingredients = data.pop('recipeingredientamount_set', None)
        if ingredients is not None:
            for ingredient in ingredients:
                ingredient_unit_pk = ingredient['ingredient_unit'].get('pk')
                ingredient_amount = ingredient.get('amount')
                if ingredient_unit_pk and ingredient_amount:
                    if not IngredientUnit.objects.filter(
                        pk=ingredient_unit_pk
                    ).exists():
                        raise serializers.ValidationError(
                            {
                                'ingredients': (f'The ingredient_unit with pk'
                                                f'{ingredient_unit_pk} '
                                                f'does not exist!')
                            }
                        )
                else:
                    raise serializers.ValidationError(
                        {
                            'ingredients': ('id or/and amount values '
                                            'are missing')
                        }
                    )
            data['ingredients'] = ingredients
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            recipe.tags.add(tag)

        for ingredient in ingredients:
            ingredient_unit_pk = ingredient['ingredient_unit']['pk']
            ingredient_unit = IngredientUnit.objects.get(pk=ingredient_unit_pk)
            RecipeIngredientAmount.objects.create(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient_unit=ingredient_unit,
            )
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            for tag in tags:
                instance.tags.add(tag)

        if ingredients is not None:
            instance.ingredients.clear()
            for ingredient in ingredients:
                ingredient_unit_pk = ingredient['ingredient_unit']['pk']
                ingredient_unit = IngredientUnit.objects.get(
                    pk=ingredient_unit_pk
                )
                RecipeIngredientAmount.objects.create(
                    recipe=instance,
                    amount=ingredient['amount'],
                    ingredient_unit=ingredient_unit,
                )

        instance.save()

        return super().update(instance, validated_data)

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
