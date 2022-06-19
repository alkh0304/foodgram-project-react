from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import CustomUser, Subscription
from .fields import Base64ImageField
from .utils import bulk_create_ingredients


class UserRegistationSerializer(UserSerializer):
    """Сериализатор модели CustomUserModels для регистрации пользователей."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'id',
                  'last_name', 'bio', 'date_joined', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user, author=obj.id).exists()


class UserCreationSerializer(UserCreateSerializer):
    """ Сериализация пользователя при регистрации """
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name',
                  'password')


class SubscriptionListSerializer(serializers.ModelSerializer):
    """ Сериализация подписок и списка подписок"""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    username = serializers.ReadOnlyField(source='author.username')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('email', 'id', 'first_name', 'last_name', 'username',
                  'recipes', 'recipes_count', 'is_subscribed')

    def to_internal_value(self, data):
        return data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return Subscription.objects.filter(author=obj.author,
                                           user=request.user).exists()

    def get_recipes_count(self, data):
        return Recipe.objects.filter(
                author=data.author).count()

    def get_recipes(self, data):
        request = self.context.get('request')
        if request.GET.get('recipes_limit'):
            limit = int(request.GET.get('recipes_limit'))
            queryset = Recipe.objects.filter(
                author=data.author)[:limit]
        else:
            queryset = Recipe.objects.filter(author=data.author)
        serializer = TinyRecipeSerializer(queryset, read_only=True,
                                          many=True)
        return serializer.data

    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)

    def validate(self, data):
        author = data['author_id']
        user = data['user_id']
        if user == author:
            raise serializers.ValidationError(
                'Оформление подписки на себя - недопустимо.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.')

        return data


class IngredientSerielizer(serializers.ModelSerializer):
    """Сериализатор отдельного ингредиента."""
    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit', 'id')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""
    class Meta:
        model = Tag
        fields = ('name', 'color', 'slug', 'id')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор списка ингредиентов в рецепте."""
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredient
        fields = ('name', 'measurement_unit', 'amount', 'id')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалиализатор создания рецептов."""
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredient_recipe')
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time', 'id')
        read_only_field = ('id', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['name', 'author']
            ),
        ]

    def create_ingredients(self, recipe, ingredients):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient=ingredient['id']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def create(self, obj):
        ingredients = obj.pop('ingredient_recipe')
        created_recipe = super().create(obj)
        bulk_create_ingredients(created_recipe, ingredients)

        return created_recipe

    def update(self, obj, validated_data):
        obj.image = validated_data.get('image', obj.image)
        obj.cooking_time = (
            validated_data.get('cooking_time', obj.cooking_time)
        )
        obj.name = validated_data.get('name', obj.name)
        obj.text = validated_data.get('text', obj.text)
        obj.tags.set(validated_data.get('tags', obj.tags))
        obj.ingredients.clear()
        obj.save()

        bulk_create_ingredients(obj,
                                validated_data['ingredient_recipe'])
        obj.save()

        return obj

    def validate(self, data):
        recipe_ingredients = self.initial_data.get('ingredients')
        unique_ingredients = []
        for ingredient in recipe_ingredients:
            ingredient_id = get_object_or_404(Ingredient, id=ingredient['id'])
            if ingredient_id not in unique_ingredients:
                unique_ingredients.append(ingredient_id)
            else:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться!')
        return data


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериалиализатор просмотра рецептов."""
    author = UserRegistationSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True, many=True, source='ingredient_recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_list = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_list', 'name', 'image', 'text',
                  'cooking_time', 'id')

    def get_is_favorited(self, obj):
        """Проверка: добавлен ли рецепт в избранное."""
        user = self.context['request'].user
        if user.is_authenticated:
            return FavoriteRecipe.objects.filter(
                user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_list(self, obj):
        """Проверка: добавлен ли рецепт в список покупок."""
        user = self.context['request'].user
        if user.is_authenticated:
            return ShoppingList.objects.filter(
                user=user, recipe=obj).exists()
        return False


class TinyRecipeSerializer(serializers.ModelSerializer):
    """Получение данных о рецептах для списка покупок и подписок."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
