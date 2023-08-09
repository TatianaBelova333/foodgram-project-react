from django.contrib import admin

from recipes.models import Color, Ingredient, MeasurementUnit, Tag


class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name')
    search_fields = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Display available colors that are not used for other tags."""
        if db_field.name == "color":
            colors_in_use = Tag.objects.values_list('color__id', flat=True)
            kwargs["queryset"] = Color.objects.exclude(id__in=colors_in_use)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = ('pk', 'name', 'slug', 'color')
    search_fields = ('name',)
    list_filter = ('color',)
    prepopulated_fields = {'slug': ['name']}


admin.site.register(Color)
admin.site.register(MeasurementUnit, MeasurementUnitAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
