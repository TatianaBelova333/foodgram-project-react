from django.urls import include, path
from django.contrib.auth import get_user_model
from rest_framework.routers import DefaultRouter

from api.views import (IngredientReadOnlyViewset,
                       TagReadOnlyViewset,
                       RecipeViewset)
from api.views import CustomUserViewSet

app_name = 'api'


router_v1 = DefaultRouter()

router_v1.register('users', CustomUserViewSet)

User = get_user_model()

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
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
