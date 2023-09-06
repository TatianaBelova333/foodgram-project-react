from django.contrib import admin

from recipes.models import (Ingredient,
                            IngredientUnit,
                            MeasurementUnit,
                            Recipe,
                            RecipeIngredientAmount,
                            Tag)


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'color')
    search_fields = ('name',)
    list_filter = ('color',)
    prepopulated_fields = {'slug': ['name']}


class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name')
    search_fields = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name')
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientMeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingredient', 'measurement_unit')
    search_fields = ('ingredient__name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientAmountInLine(admin.TabularInline):
    model = RecipeIngredientAmount
    raw_id_fields = ('ingredient_unit',)


class RecipeAdmin(admin.ModelAdmin):

    list_display = (
        'pk',
        'name',
        'author',
        'display_tags',
        'display_cart_adds_number',
        'display_favorites_adds_number',
    )
    search_fields = ('name',)
    list_filter = ('author', 'name')
    inlines = (RecipeIngredientAmountInLine,)


admin.site.register(MeasurementUnit, MeasurementUnitAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(IngredientUnit, IngredientMeasurementUnitAdmin)
admin.site.register(Recipe, RecipeAdmin)
