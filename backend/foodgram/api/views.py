from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import CustomUser
from .filters import CustomFilter
from .pagination import RecipePagination
from .permissions import AuthorOrReadOnly
from .serializers import (IngredientSerielizer,
                          RecipeCreateSerializer, RecipeViewSerializer,
                          SubscriptionSerializer, TagSerializer,
                          TinyRecipeSerializer, UserRegistationSerializer)
from .utils import convert_pdf


class UserViewSet(DjoserUserViewSet):
    """CRUD user models."""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['username']
    lookup_field = 'username'

    @action(
        detail=False,
        methods=['get', 'put', 'patch'],
        url_path='me',
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """API для редактирования текущим пользователем своих данных."""
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(partial=True)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Запросы о подписке на авторов."""
    permission_classes = [permissions.IsAuthenticated]
    model_class = CustomUser
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        current_user = self.request.user
        return current_user.subscriber.all()

    def perform_create(self, serializer):
        author = get_object_or_404(CustomUser, pk=self.kwargs.get('pk'))
        user = self.request.user
        serializer.save(author=author, user=user)


class IngredientViewset(viewsets.ModelViewSet):
    """Отдельные ингредиенты и их список."""
    serializer_class = IngredientSerielizer
    permission_classes = [permissions.AllowAny]
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (SearchFilter, )
    search_fields = ('name', )


class TagViewset(viewsets.ModelViewSet):
    """Отдельные тэги и их список."""
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    pagination_class = None


class RecipeViewset(viewsets.ModelViewSet):
    """
    Обработка запросов о рецептах, просмотр, создание,
    изменение, удаление.
    """
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_class = CustomFilter
    pagination_class = RecipePagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            permission_classes = [permissions.AllowAny]
        elif self.action in ('update', 'destroy', 'partial_update'):
            permission_classes = [AuthorOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == 'POST' or self.request.method == 'PATCH':
            return RecipeCreateSerializer
        return RecipeViewSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def new_recipe(self, model, request, pk):
        user = self.request.user
        current_recipe = get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(recipe=current_recipe, user=user).exists():
            return Response(
                'Рецепт уже добавлен', status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(recipe=current_recipe, user=user)
        serializer = TinyRecipeSerializer(current_recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def remove_recipe(self, model, request, pk):
        user = self.request.user
        current_recipe = get_object_or_404(Recipe, pk=pk)
        obj = get_object_or_404(model, recipe=current_recipe, user=user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=['post', 'delete'],
        url_path='shopping_cart',
    )
    def shopping_list(self, request, pk):
        if request.method == 'POST':
            return self.new_recipe(ShoppingList, request, pk)
        else:
            return self.remove_recipe(ShoppingList, request, pk)

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=['post', 'delete'],
        url_path='favorite',
    )
    def favorite_recipe(self, request, pk=None):
        if request.method == 'POST':
            return self.new_recipe(FavoriteRecipe, request, pk)
        else:
            return self.remove_recipe(FavoriteRecipe, request, pk)

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['get', ],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        ingredient_list = {}
        list = RecipeIngredient.objects.filter(
            recipe__shopping_list__user=request.user).values_list(
            'ingredient__name', 'ingredient__measurement_unit',
            'amount'
        )
        for item in list:
            name = item[0]
            if name not in ingredient_list:
                ingredient_list[name] = {
                    'measurement_unit': item[1],
                    'amount': item[2]
                }
            else:
                ingredient_list[name]['amount'] += item[2]

        file = convert_pdf(ingredient_list, 'Список покупок')

        return FileResponse(
            file,
            as_attachment=True,
            filename='shopping_list.pdf',
            status=status.HTTP_200_OK
        )
