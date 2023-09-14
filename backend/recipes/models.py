from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from pytils.translit import slugify

User = get_user_model()


class NameBaseModel(models.Model):
    """Abstract model for classes with name field.."""
    LETTER_CASES = {
        'capitalize': str.capitalize,
        'lowercase': str.lower,
    }
    STR_LIMIT = 50
    DEFAULT_LETTERCASE = 'capitalize'

    is_cleaned = False

    name = models.CharField(
        'Название',
        max_length=200,
        unique=True,
        db_index=True,
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name[:self.STR_LIMIT]

    def clean(self):
        """
        Raise ValidationError if the name (case-insensitive) already exists.

        """
        self.is_cleaned = True

        self.name = self.LETTER_CASES[self.DEFAULT_LETTERCASE](self.name)

        instance_exists = self.__class__.objects.filter(pk=self.pk).first()

        if not instance_exists or instance_exists.name != self.name:
            if self.__class__.objects.filter(
                name=self.name,
            ).exists():
                raise ValidationError(
                    {'name': 'Данное название уже сущуествует.'}
                )

    def save(self, *args, **kwargs):
        """
        Convert the case of the name value to the default letter case
        before saving in db for consistency.

        """
        if not self.is_cleaned:
            self.full_clean()
        super().save(*args, **kwargs)


class MeasurementUnit(NameBaseModel):
    """Model for units of measurement for ingredients."""
    DEFAULT_LETTERCASE = 'lowercase'

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'


class Ingredient(NameBaseModel):
    """Model for recipe ingredients."""

    measurement_units = models.ManyToManyField(
        MeasurementUnit,
        verbose_name='Единица измерения',
        related_name='ingredients',
        through='IngredientUnit',
    )

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class IngredientUnit(models.Model):
    """
    Model for many-to-many relationship between
    Ingredient and MeausurementUnit models.

    """
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    measurement_unit = models.ForeignKey(
        MeasurementUnit,
        on_delete=models.CASCADE,
        verbose_name='Единица измерения',
    )

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Ингредиент с единицой измерения'
        verbose_name_plural = 'Ингредиенты с единицами измерения'
        ordering = ('ingredient', 'measurement_unit')
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'measurement_unit'),
                name='unique_ingredient_unit',
            )
        ]

    def __str__(self):
        return f'{self.ingredient}({self.measurement_unit})'


class Tag(NameBaseModel):
    """Model for recipes tags."""
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[А-Яа-я]+$',
                message='Название тега может состоять только из одного слова, '
                        'содержащего кириллицу.',
                code='invalid_name'
            )
        ]
    )
    color = ColorField(
        'Цвет тега',
        default='#FF0000',
        unique=True,

    )
    slug = models.SlugField(
        'slug',
        max_length=200,
        unique=True,
        blank=True,
    )

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def clean(self):
        """
        Validate that the color HEX-code is unique (case-insensitive).

        """
        super().clean()
        self.color = self.color.upper()
        instance_exists = self.__class__.objects.filter(pk=self.pk).first()
        if not instance_exists or instance_exists.color != self.color:
            if self.__class__.objects.filter(
                color=self.color,
            ).exists():
                raise ValidationError(
                    {'color': 'Данный HEX-код уже занят.'}
                )

    def save(self, *args, **kwargs):
        """
        Create slug from the color field value
        truncated to the max_length specified by the slug field
        if the slug field left blank.

        """
        if not self.slug:
            max_length = self.__class__._meta.get_field('slug').max_length
            self.slug = slugify(self.name)[:max_length]
        super().save(*args, **kwargs)


class Recipe(models.Model):
    """Model for food recipes."""
    name = models.CharField(
        'Название',
        max_length=200,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    text = models.TextField('Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин.)',
        validators=(
            MinValueValidator(
                limit_value=1,
                message='Время приготовления должно быть больше 0.',
            ),
            MaxValueValidator(
                limit_value=360,
                message='Время приготовления должно быть не более 360 мин.'
            )
        )
    )
    ingredients = models.ManyToManyField(
        IngredientUnit,
        verbose_name='Игриедиенты с ед. измер.',
        related_name='recipes',
        through='RecipeIngredientAmount',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    image = models.ImageField(
        'Избражение рецепта',
        upload_to='recipes/images/',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    shopping_cart_adds = models.ManyToManyField(
        User,
        verbose_name='В корзине',
        related_name='shopping_cart',
        blank=True,
    )
    adds_to_favorites = models.ManyToManyField(
        User,
        verbose_name='Избранное',
        related_name='favorites',
        blank=True,
    )

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', 'name')
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'name'),
                name='unique_author_recipe_name',
            )
        ]

    def __str__(self):
        return f'Рецепт "{self.name}"({self.author})'

    def save(self, *args, **kwargs):
        """
        Capitalize the recipe name before saving for consistency.

        """
        self.name = self.name.capitalize()
        super().save(*args, **kwargs)

    def display_tags(self):
        """Display all tags in a single line in the admin panel."""
        return ', '.join(map(str, self.tags.all()))

    def display_cart_adds_number(self):
        return self.shopping_cart_adds.count()

    def display_favorites_adds_number(self):
        return self.adds_to_favorites.count()

    display_tags.short_description = 'Теги'
    display_cart_adds_number.short_description = 'Кол-во добавлений в корзину'
    display_favorites_adds_number.short_description = ('Кол-во добавлений '
                                                       'в избранное')


class RecipeIngredientAmount(models.Model):
    """
    Model for many-to-many relationship between
    Recipe and IngredientUnit models.

    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient_unit = models.ForeignKey(
        IngredientUnit,
        on_delete=models.PROTECT,
        verbose_name='Ингредиент с ед.изм.',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(
                limit_value=1,
                message='Количество должно быть целым числом больше 0.',
            ),
            MaxValueValidator(
                limit_value=2000,
                message='Количество должно не более 2000.'
            )
        )
    )

    class Meta:
        verbose_name = 'Ингредиент, ед. измер., кол-во'
        verbose_name_plural = 'Ингредиенты, ед. измер., кол-во'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient_unit'),
                name='unique_recipe_ingredient_unit',
            )
        ]

    def __str__(self):
        return f'{self.recipe}, {self.ingredient_unit}, {self.amount}'
