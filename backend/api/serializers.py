from rest_framework import serializers

from recipes.models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Ingredient model serializer."""
    measurement_unit = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
