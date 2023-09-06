from django.contrib.auth import get_user_model
from django.db.models import Case, When
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsObjOwnerOrAdminOrReadOnly
from api.serializers import (IngredientUnitSerializer,
                             RecipeBriefInfoSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeListDetailSerializer,
                             TagSerializer)
from recipes.models import IngredientUnit, Recipe, Tag
from users.models import Subscription

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """
    Extends the Djoser UserViewSet.

    Additional endpoints:

    subscribe:
    Add/remove the given user to/from the request user's subscriptions.

    subscriptions:
    Return a list of all exisiting request user's subscriptions.

    """
    def get_serializer_class(self):
        if self.action in ('subscriptions', 'subscribe'):
            return settings.SERIALIZERS.subscriptions
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        if self.action == 'subscriptions':
            return user.subscriptions.all()
        return super().get_queryset()

    @action(["post", "delete"],
            detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        recipe_author = self.get_object()
        current_user = self.get_instance()
        subcription = Subscription.objects.filter(
            user=current_user,
            author=recipe_author
        )
        if request.method == 'POST':
            if recipe_author != current_user:
                if not subcription.exists():
                    Subscription.objects.create(
                        user=current_user, author=recipe_author
                    )
                    serializer = self.get_serializer(subcription.first()).data
                    return Response(
                        status=status.HTTP_201_CREATED,
                        data=serializer,
                    )
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'errors': (f'Пользователь {current_user.username} уже '
                                   f'подписан на {recipe_author.username}'),
                    })
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'errors': ('Текущий пользователь не может '
                               'подписываться на себя'),
                })

        elif request.method == 'DELETE':
            if subcription.exists():
                subcription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={
                                'errors': (f'Пользователь '
                                           f'{current_user.username} '
                                           f'уже подписан на '
                                           f'{recipe_author.username}'),
                            })

    @action(["get"],
            detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class IngredientReadOnlyViewset(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Return a list of all ingredients with measurement units.

    retrieve:
    Return the given ingredient with the measurement unit.

    """
    queryset = IngredientUnit.objects.all()
    serializer_class = IngredientUnitSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (IsAuthenticatedOrReadOnly,)


class TagReadOnlyViewset(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Return a list of all existing recipe tags.

    retrieve:
    Return the given recipe tag.

    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (IsAuthenticatedOrReadOnly,)


class RecipeViewset(viewsets.ModelViewSet):
    """
    list:
    Return a list of all existing recipes filtered by pub_date
    in descending order.

    retrieve:
    Return the given recipe.

    create:
    Create and return a new Recipe instance.

    destroy:
    Delete the given recipe.

    partial_update:
    Update the given recipe.

    favorite:
    Add/delete the given recipe to/from the request user's favorites.

    shopping_cart:
    Add/delete the given recipe to/from the request user's shopping_cart.

    download_shopping_cart:
    Download a text file with all ingredients
    and their amounts from the shopping cart recipes.

    """

    serializer_class = RecipeListDetailSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsObjOwnerOrAdminOrReadOnly,)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            user_favorites = []
            user_shopping_cart = []
        else:
            user_favorites = self.request.user.favorites.all()
            user_shopping_cart = self.request.user.shopping_cart.all()

        queryset = Recipe.objects.select_related(
            'author',
        ).prefetch_related(
            'tags',
            'ingredients',
        ).annotate(
            is_favorited=Case(
                When(
                    id__in=user_favorites,
                    then=True,
                ),
                default=False,
            )
        ).annotate(
            is_in_shopping_cart=Case(
                When(
                    id__in=user_shopping_cart,
                    then=True,
                ),
                default=False,
            )
        )
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeCreateUpdateSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return RecipeBriefInfoSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Add/delete the given recipe to/from the request user's favorites."""
        recipe = self.get_object()
        user_items_name = 'favorites'
        return self.__handle_extra_action(request, recipe, user_items_name)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """
        Add/delete the given recipe to/from
        the request user's shopping_cart.

        """
        recipe = self.get_object()
        user_items_name = 'shopping_cart'
        return self.__handle_extra_action(request, recipe, user_items_name)

    @action(methods=['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request, pk=None):
        """
        Download a text file with ingredients and their amounts
        from the shopping cart recipes.

        """
        shopping_cart_data = self.__get_shopping_cart_ingredients(
            self.request.user
        )
        readable_data = self.convert_to_readable_data(shopping_cart_data)
        response = HttpResponse(
            readable_data,
            headers={
                "Content-Type": "text/plain",
                "Content-Disposition": ('attachment; '
                                        'filename="ingredients.txt"'),
            },
        )
        return response

    def __handle_extra_action(self, request, recipe, user_items_name):
        user = self.request.user

        user_items = {
            'shopping_cart': user.shopping_cart,
            'favorites': user.favorites,
        }
        user_items_set = user_items[user_items_name]

        if request.method == 'POST':
            return self.__add_to_user_items(
                user, recipe, user_items_set,
            )
        if request.method == 'DELETE':
            return self.__remove_from_user_items(
                user, recipe, user_items_set
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def __add_to_user_items(self, user, recipe, user_items_set):
        error_message = f'Рецепт "{recipe.name}" уже добавлен.'

        if recipe not in user_items_set.all():
            user_items_set.add(recipe)
            user.save()
            serializer = self.get_serializer(recipe).data
            return Response(
                status=status.HTTP_201_CREATED,
                data=serializer,
            )

        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={
                            'errors': error_message,
                        })

    def __remove_from_user_items(self, user, recipe, user_items_set):
        error_message = f'Рецепт "{recipe.name}" уже удален.'

        if recipe in user_items_set.all():
            user_items_set.remove(recipe)
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={
                            'errors': error_message,
                        })

    def __get_shopping_cart_ingredients(self, user: User) -> dict[str, int]:
        """
        Return a dict with ingredients and their total amounts
        from the request user's shopping cart.

        """
        recipes_in_cart = user.shopping_cart.all()
        #  Collect ingredients from all recipes in user's shopping cart
        ingr_with_qty = []
        for recipe in recipes_in_cart:
            ingr_with_qty.extend(
                recipe.recipeingredientamount_set.all()
            )
        #  Sum up the amounts of the duplicate inredients
        ingr_with_tot_qty = {}
        for ingr in ingr_with_qty:
            ingr_with_tot_qty[ingr.ingredient_unit] = (ingr_with_tot_qty.get(
                ingr.ingredient_unit, 0) + ingr.amount)

        return ingr_with_tot_qty

    @staticmethod
    def convert_to_readable_data(
        ingredients_with_qty: dict[str, int]
    ) -> list[str]:
        """Convert data into a list of strings."""
        readable_data = []
        for ingredient in ingredients_with_qty.items():
            ingredient_unit, amount = ingredient
            readable_data.append(f'{ingredient_unit}: {amount}\n')
        return sorted(readable_data)
