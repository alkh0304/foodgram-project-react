from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import CustomUser, Subscription


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


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
    quantity = serializers.IntegerField(source='quantity')
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredient
        fields = ('name', 'measurement_unit', 'quantity', 'id')


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
                quantity=ingredient['quantity'],
                ingredient=ingredient['id']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def create(self, data):
        tags = data.pop('tags')
        image = data.pop('image')
        ingredients = data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, data, recipe):
        tags = data.pop('tags')
        ingredients = data.pop('ingredients')
        recipe.tags.clear()
        recipe.tags.set(tags)
        recipe.ingredients.all().delete()
        self.create_ingredients(ingredients, recipe)
        super().update(recipe, data)
        return recipe

    def validate(self, data):
        recipe_ingredients = data['ingredients']
        unique_ingredients = []
        for ingredient in recipe_ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id not in unique_ingredients:
                unique_ingredients.append(ingredient_id)
            else:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться!')
        recipe_tags = data['tags']
        unique_tags = []
        for tag in recipe_tags:
            tag_id = tag['id']
            if tag_id not in unique_tags:
                unique_tags.append(tag_id)
            else:
                raise serializers.ValidationError(
                    'Теги не должны повторяться!')
        return data


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериалиализатор просмотра рецептов."""
    author = UserSerializer(read_only=True)
    tag = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True, many=True, source='ingredient_recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('tag', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time', 'id')

    def get_is_favorited(self, obj):
        """Проверка: добавлен ли рецепт в избранное."""
        user = self.context['request'].user
        if user.is_authenticated:
            return FavoriteRecipe.objects.filter(
                user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверка: добавлен ли рецепт в список покупок."""
        user = self.context['request'].user
        if user.is_authenticated:
            return ShoppingList.objects.filter(
                user=user, recipe=obj).exists()
        return False


class TinyRecipeSerializer(serializers.ModelSerializer):
    """Получение данных о рецептах для списка покупок и подписок."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('name', 'image', 'cooking_time', 'id')
