from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientReadOnlyViewset

app_name = 'api'


router_v1 = DefaultRouter()
router_v1.register(
    'ingredients', IngredientReadOnlyViewset, basename='ingredients'
)

urlpatterns = [
    path('', include(router_v1.urls)),
]
