from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import CustomUser, Subscription
from .fields import Base64ImageField
from .utils import add_ingredients_to_recipe


class UserRegistationSerializer(UserSerializer):
    """Сериализатор модели CustomUserModels для регистрации пользователей."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'date_joined', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj.id).exists()


class UserCreationSerializer(UserCreateSerializer):
    """ Сериализация пользователя при регистрации """
    class Meta:
        model = CustomUser
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )


class SubscriptionListSerializer(UserRegistationSerializer):
    """ Сериализация списка на кого подписан пользователь"""
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request.GET.get('recipes_limit'):
            recipe_limit = int(request.GET.get('recipes_limit'))
            queryset = Recipe.objects.filter(
                author=obj.author)[:recipe_limit]
        else:
            queryset = Recipe.objects.filter(
                author=obj.author)
        serializer = TinyRecipeSerializer(
            queryset, read_only=True, many=True
        )
        return serializer.data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        get_object_or_404(CustomUser, username=data['author'])
        if self.context['request'].user == data['author']:
            raise serializers.ValidationError('Сам на себя подписываешься!')
        if Subscription.objects.filter(
                user=self.context['request'].user,
                author=data['author']
        ):
            raise serializers.ValidationError('Уже подписан')
        return data

    def to_representation(self, instance):
        return SubscriptionListSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data


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

    def create(self, data):
        ingredients = data.pop('ingredient_recipe')
        new_recipe = super().create(data)
        add_ingredients_to_recipe(new_recipe, ingredients)

        return new_recipe

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

        add_ingredients_to_recipe(obj,
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

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data["image"] = obj.image.url
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

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data["image"] = obj.image.url
        return data


class TinyRecipeSerializer(serializers.ModelSerializer):
    """Получение данных о рецептах для списка покупок и подписок."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ['name', 'image', 'cooking_time']
