from django_filters.rest_framework import FilterSet, BooleanFilter, CharFilter
from django.db.models import Q

from recipes.models import Recipe


class IngredientFilter(FilterSet):
    """
    Filter IngredientUnit queryset by ingredient name
    (case-insensitive starts-with or case-insensitive containment test).

    """
    name = CharFilter(
        field_name="ingredient__name",
        method='filter_ingredient_name',
    )

    def filter_ingredient_name(self, queryset, field_name, value):
        primary_lookup = '__'.join([field_name, 'istartswith'])
        secondary_lookup = '__'.join([field_name, 'icontains'])
        return (queryset.filter(Q(**{primary_lookup: value})
                                | Q(**{secondary_lookup: value})))


class RecipeFilter(FilterSet):
    """
    Filter Recipe queryset by author id, tag slug,
    is_favorited and is_in_shopping_cart fields.

    """
    is_favorited = BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = BooleanFilter(field_name='is_in_shopping_cart')
    tags = CharFilter(
        field_name='tags__slug',
        method='filter_by_tag_slug',
    )

    class Meta:
        model = Recipe
        fields = ['author']

    def filter_by_tag_slug(self, queryset, field_name, value):
        """Filter and return a queryset of all Recipe instances
        that contain at least one tag from the 'tags' query params.

        """
        tags = self.request.GET.getlist('tags', None)
        lookup = '__'.join([field_name, 'in'])
        queryset = queryset.filter(**{lookup: tags}).distinct()
        return queryset
