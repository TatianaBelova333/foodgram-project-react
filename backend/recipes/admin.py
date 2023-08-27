from django.contrib import admin

from recipes.models import (TagColor, Ingredient, MeasurementUnit,
                            Tag, IngredientUnit, Recipe,
                            RecipeIngredientAmount)


class TagInline(admin.TabularInline):
    model = Tag
    raw_id_fields = ["color"]


class TagColorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    inlines = [TagInline]


class TagAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Display all available colors that are not being used for other tags.

        """
        if db_field.name == "color":
            colors_in_use = Tag.objects.values_list('color__id', flat=True)
            kwargs["queryset"] = TagColor.objects.exclude(id__in=colors_in_use)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
    raw_id_fields = ["ingredient_unit"]


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
    inlines = [RecipeIngredientAmountInLine]


admin.site.register(TagColor, TagColorAdmin)
admin.site.register(MeasurementUnit, MeasurementUnitAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(IngredientUnit, IngredientMeasurementUnitAdmin)
admin.site.register(Recipe, RecipeAdmin)
