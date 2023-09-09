import factory
import factory.fuzzy
from django.contrib.auth import get_user_model

from recipes.models import (Tag, IngredientUnit,
                            Ingredient, MeasurementUnit,
                            Recipe, RecipeIngredientAmount)
from users.models import Subscription

User = get_user_model()


class TagFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Tag

    name = factory.fuzzy.FuzzyText(
        chars='абвгдежзийклмнопрстуфхцчшщъыьэюя'
    )
    color = factory.Iterator([
        '#A4FF26',
        '#48FF9D',
        '#63F2FF',
        '#FF1BEB',
        '#EFFFCC',
        '#C5C7FF',
        '#EEB5FF',
        '#FF6385',
        '#EBC8FF',
    ])
    slug = factory.Sequence(lambda n: f'breakfast{n}')


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User

    first_name = "Vasily"
    last_name = "Ivanov"
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'person{n}@example.com')
    password = factory.django.Password('test_password123')


class MeasurementUnitFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = MeasurementUnit

    name = factory.Sequence(lambda n: f'kg{n}')


class IngredientFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Ingredient

    name = factory.Sequence(lambda n: f'water{n}')


class IngredientUnitFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = IngredientUnit

    ingredient = factory.SubFactory(IngredientFactory)
    measurement_unit = factory.SubFactory(MeasurementUnitFactory)


class RecipeFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Recipe

    name = factory.Sequence(lambda n: f'pasta{n}')
    author = factory.SubFactory(UserFactory)
    text = 'test recipe description'
    cooking_time = 5

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tags.add(*extracted)


class RecipeIngredientAmountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecipeIngredientAmount

    recipe = factory.SubFactory(RecipeFactory)
    ingredient_unit = factory.SubFactory(IngredientUnitFactory)
    amount = 10


class RecipeWithIngredientAmountFactory(RecipeFactory):
    ingredient_set1 = factory.RelatedFactory(
        RecipeIngredientAmountFactory,
        factory_related_name='recipe',
        ingredient_unit__ingredient__name=factory.Sequence(
            lambda n: f'Ingredient{n}'
        ),
    )
    ingredient_set2 = factory.RelatedFactory(
        RecipeIngredientAmountFactory,
        factory_related_name='recipe',
        ingredient_unit__ingredient__name=factory.Sequence(
            lambda n: f'Ingredient{n}'
        ),
    )

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tags.add(*extracted)

    @factory.post_generation
    def shopping_cart_adds(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.shopping_cart_adds.add(*extracted)

    @factory.post_generation
    def adds_to_favorites(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.adds_to_favorites.add(*extracted)


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    user = factory.SubFactory(UserFactory)
    author = factory.SubFactory(UserFactory)
