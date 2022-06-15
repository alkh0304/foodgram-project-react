from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """Пагинация рецептов"""
    page_size = 6
    page_size_query_param = 'limit'
