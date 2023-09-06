from django.contrib.auth import get_user_model
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    CustomUserViewSet,
    IngredientReadOnlyViewset,
    RecipeViewset,
    TagReadOnlyViewset,
)

app_name = 'api'
User = get_user_model()

router_v1 = DefaultRouter()
router_v1.register('users', CustomUserViewSet)
router_v1.register(
    'ingredients', IngredientReadOnlyViewset, basename='ingredients',
)
router_v1.register(
    'tags', TagReadOnlyViewset, basename='tags',
)
router_v1.register(
    'recipes', RecipeViewset, basename='recipes',
)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
