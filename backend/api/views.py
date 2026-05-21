from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse

from recipes.models import (
    Tag, Ingredient, Recipe, RecipeIngredient
)
from users.models import User
from api.serializers import (
    TagSerializer, IngredientSerializer, RecipeSerializer,
    RecipeCreateSerializer, SubscriptionSerializer, Base64ImageField
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_id=author)
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited and self.request.user.is_authenticated:
            queryset = queryset.filter(
                favorites__user=self.request.user
            )
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_in_shopping_cart and self.request.user.is_authenticated:
            queryset = queryset.filter(
                shopping_cart__user=self.request.user
            )
        return queryset

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            request.user.favorites.get_or_create(recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        request.user.favorites.filter(recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            request.user.shopping_cart.get_or_create(recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        request.user.shopping_cart.filter(recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        text = ''
        for item in ingredients:
            text += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) "
                f"— {item['total']}\n"
            )
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(
            subscribers__user=self.request.user
        )

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            request.user.subscriptions.get_or_create(author=author)
            return Response(status=status.HTTP_201_CREATED)
        request.user.subscriptions.filter(author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def avatar_view(request):
    user = request.user
    if request.method == 'PUT':
        avatar_data = request.data.get('avatar')
        if avatar_data:
            field = Base64ImageField()
            user.avatar = field.to_internal_value(avatar_data)
            user.save()
        return Response(
            {'avatar': (
                request.build_absolute_uri(user.avatar.url)
                if user.avatar else None
            )}
        )
    elif request.method == 'DELETE':
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
