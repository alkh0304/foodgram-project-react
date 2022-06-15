from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag


class CustomFilter(filters.FilterSet):
    """
    Набор фильтров для получения списка рецептов согласно заданным в
    query_param фильтрам. Доступна фильтрация по избранному, автору, списку
    покупок и тегам.
    """

    author = filters.NumberFilter(field_name='author__id', lookup_expr='exact')
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             queryset=Tag.objects.all(),
                                             to_field_name='slug')
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value is True:
            return queryset.filter(
                users_favorite__user=self.request.user)
        return queryset

    def get_is_in_shopping_list(self, queryset, name, value):
        if self.request.user.is_authenticated and value is True:
            return queryset.filter(
                shopping_list__user=self.request.user)
        return queryset
