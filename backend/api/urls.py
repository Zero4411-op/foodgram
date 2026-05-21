from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    TagViewSet, IngredientViewSet, RecipeViewSet,
    SubscriptionViewSet, avatar_view
)

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)
router.register('users/subscriptions',
                SubscriptionViewSet, basename='subscriptions'
                )

urlpatterns = [
    path('users/me/avatar/', avatar_view, name='avatar'),
    path(
        'users/<int:pk>/subscribe/',
        SubscriptionViewSet.as_view(
            {'post': 'subscribe', 'delete': 'subscribe'}
        ),
        name='subscribe'
    ),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
