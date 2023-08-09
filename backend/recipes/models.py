from django.db import models
from django.core.exceptions import ValidationError

from pytils.translit import slugify


class NameBaseModel(models.Model):
    """Abstract model for classes with name field.."""
    LETTER_CASES = {
        'capitalize': str.capitalize,
        'lowercase': str.lower,
    }
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
        return self.name

    def clean(self):
        """
        Raise ValidationError if the name (case-insensitive) already exists.

        """
        self.is_cleaned = True
        name = self.LETTER_CASES[self.default_lettercase](self.name)

        if self.__class__.objects.filter(
            name=name,
        ).exists():
            raise ValidationError('This name already exists.')

    def save(self, *args, **kwargs):
        """
        Convert the case of a name to the default letter case
        before saving for consistency.

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
        on_delete=models.SET_NULL,
        verbose_name='Единица измерения',
        related_query_name='ingredients',
        through='IngredientMeasurementUnit',
    )

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class IngredientMeasurementUnit(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    measurement_unit = models.ForeignKey(
        MeasurementUnit, on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.ingredient} {self.measurement_unit}'


class Color(NameBaseModel):
    default_lettercase = 'lowercase'

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Цвет'
        verbose_name_plural = 'Цвета'


class Tag(NameBaseModel):
    color = models.OneToOneField(
        Color,
        on_delete=models.PROTECT,
        verbose_name='Цвет',
        related_query_name='tags',
        unique=True,
    )
    slug = models.SlugField(
        'slug',
        max_length=200,
        unique=True,
        blank=True,
    )

    class Meta(NameBaseModel.Meta):
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

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
