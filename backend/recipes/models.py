from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

from pytils.translit import slugify
import webcolors

User = get_user_model()


class NameBaseModel(models.Model):
    """Abstract model for classes with name field.."""
    LETTER_CASES = {
        'capitalize': str.capitalize,
        'lowercase': str.lower,
    }
    STR_LIMIT = 50

    default_lettercase = 'capitalize'
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
        name = self.LETTER_CASES[self.default_lettercase](self.name)

        if self.__class__.objects.filter(
            name=name,
        ).exists():
            raise ValidationError('Данное название уже существует.')

    def save(self, *args, **kwargs):
        """
        Convert the case of a name to the default letter case
        before saving in db for consistency.

        """
        if not self.is_cleaned:
            self.full_clean()
        self.name = self.LETTER_CASES[self.default_lettercase](self.name)
        super().save(*args, **kwargs)


class MeasurementUnit(NameBaseModel):
    default_lettercase = 'lowercase'

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'


class Ingredient(NameBaseModel):

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

    def __str__(self):
        return f'{self.ingredient}({self.measurement_unit})'


class TagColor(NameBaseModel):
    default_lettercase = 'lowercase'

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Цвет тега'
        verbose_name_plural = 'Цвета тегов'

    def clean(self):
        """
        Raise ValidationError if the HEX-code for the color name
        does not exist.

        """
        try:
            webcolors.name_to_hex(self.name)
        except ValueError:
            raise ValidationError('HEX-код для данноге цвета не существует.')

        super().clean()


class Tag(NameBaseModel):
    color = models.OneToOneField(
        TagColor,
        on_delete=models.PROTECT,
        verbose_name='Цвет',
        related_name='tags',
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

    def save(self, *args, **kwargs):
        """
        Create slug from the color field value
        truncated to the max_length specified by the slug field
        if the slug field left blank.

        """
        if not self.slug:
            max_length = self.__class__._meta.get_field('slug').max_length
            self.slug = slugify(self.title)[:max_length]
        super().save(*args, **kwargs)


class Recipe(models.Model):
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
        validators=[MinValueValidator(
            limit_value=1,
            message='Время приготовления должно быть больше 0.'
        )]
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

    def __str__(self):
        return f'Рецепет "{self.name}"({self.author})'

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
        validators=[MinValueValidator(
            limit_value=1,
            message='Количество должно быть больше 0.',
        )]
    )

    class Meta:
        verbose_name = 'Ингредиент, ед. измер., кол-во'
        verbose_name_plural = 'Ингредиенты, ед. измер., кол-во'

    def __str__(self):
        return f'{self.recipe}, {self.ingredient_unit}, {self.amount}'
