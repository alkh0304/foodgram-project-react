from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router_v1 = DefaultRouter()
router_v1.register('tags', views.TagViewset, basename='tag')
router_v1.register('ingredients', views.IngredientViewset,
                   basename='ingredient')
router_v1.register('recipes', views.RecipeViewset, basename='recipe')
router_v1.register('users', views.UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/subscriptions/', views.SubscriptionListView.as_view(),
         name='subscriptions'),
    path('users/<int:user_id>/subscribe/', views.SubscriptionViewSet.as_view(),
         name='subscribe'),
]
