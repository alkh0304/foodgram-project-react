from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    search_param = 'name'


class CustomFilter(filters.FilterSet):
    """
    Набор фильтров для рецептов.
    """

    author = filters.NumberFilter(field_name='author__id', lookup_expr='exact')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart_filter')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited_filter(self, queryset, name, value):
        if value:
            return queryset.filter(users_favorite__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart_filter(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset
