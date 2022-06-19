from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import CustomUser, Subscription
from .utils import add_ingredients_to_recipe


class UserRegistationSerializer(DjoserUserSerializer):
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


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    user = serializers.SlugRelatedField(
        queryset=CustomUser.objects.all(),
        slug_field='username',
    )

    class Meta:
        fields = ('username', 'email', 'first_name',
                  'last_name', 'id')
        model = Subscription
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author']
            ),
        ]

    def validate(self, data):
        """Проверка подписки на себя и повторной подписки."""
        if self.context['request'].user == data['author']:
            raise serializers.ValidationError(
                "Подписка на себя невозможна.")

        if Subscription.objects.filter(user=data['user'],
                                       user_author=data['author']).exists():
            raise serializers.ValidationError(
                "Повторная подписка невозможна.")

        return data

    def create(self, validated_data):
        """Добавление подписки."""
        current_user = validated_data['user']
        author = validated_data['author']
        Subscription.objects.create(user=current_user, author=author)

        return current_user


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
    image = Base64ImageField(max_length=None)

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

    def create(self, vaidated_data):
        ingredients = self.initial_data.pop('ingredients')
        image = vaidated_data.pop('image')
        tags = vaidated_data.pop('tags')
        recipe = Recipe.objects.create(image=image, **vaidated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

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
        fields = ('name', 'image', 'cooking_time', 'id')
