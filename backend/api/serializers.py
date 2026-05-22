import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (
    Tag, Ingredient, Recipe, RecipeIngredient
)
from users.models import User

MAX_AMOUNT = 32000
MIN_AMOUNT = 1


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.subscriptions.filter(
                author=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text', 'ingredients',
            'tags', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.favorites.filter(
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.shopping_cart.filter(
                recipe=obj
            ).exists()
        return False


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT, max_value=MAX_AMOUNT
    )


class RecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    ingredients = IngredientAmountSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_AMOUNT, max_value=MAX_AMOUNT
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'ingredients',
            'tags', 'cooking_time'
        )

    def validate_cooking_time(self, value):
        if value < MIN_AMOUNT:
            raise serializers.ValidationError(
                'Время приготовления должно быть не менее 1 минуты.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        for ingredient in value:
            if ingredient['amount'] < MIN_AMOUNT:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть не менее 1.'
                )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(instance, ingredients_data)
        return instance

    @staticmethod
    def _create_ingredients(recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        ])


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.subscriptions.filter(
                author=obj
            ).exists()
        return False

    def get_recipes(self, obj):
        recipes = obj.recipes.all()[:3]
        return [
            {
                'id': r.id,
                'name': r.name,
                'image': r.image.url if r.image else None,
                'cooking_time': r.cooking_time,
            }
            for r in recipes
        ]
