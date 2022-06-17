from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import CustomUser
from .filters import CustomFilter
from .pagination import RecipePagination
from .permissions import AuthorOrReadOnly
from .serializers import (CustomTokenSerializer, IngredientSerielizer,
                          RecipeCreateSerializer, RecipeViewSerializer,
                          SubscriptionSerializer, TagSerializer,
                          TinyRecipeSerializer, UserSerializer)
from .utils import convert_pdf


class UserViewSet(viewsets.ModelViewSet):
    """CRUD user models."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['username']
    lookup_field = 'username'

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


class CustomTokenView(TokenViewBase):
    """Получение токена взамен username."""
    serializer_class = CustomTokenSerializer
    permission_classes = [permissions.AllowAny]


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
    permission_classes = [AuthorOrReadOnly]
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_class = CustomFilter
    pagination_class = RecipePagination

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
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(ingredient_total=Sum('quantity'))

        file = convert_pdf(ingredients, 'Список покупок')

        return FileResponse(
            file,
            as_attachment=True,
            filename='shopping_list.pdf',
            status=status.HTTP_200_OK
        )
