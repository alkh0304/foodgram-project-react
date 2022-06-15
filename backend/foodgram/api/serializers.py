from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredients, ShoppingList, Tag)
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import CustomUser, Subscription


class UserRegistationSerializer(serializers.ModelSerializer):
    """Сериализатор модели CustomUserModels для регистрации пользователей."""
    class Meta:
        model = CustomUser
        fields = ('username', 'email')
        read_only_fields = ['password']
        validators = [
            UniqueTogetherValidator(
                queryset=CustomUser.objects.all(),
                fields=['username', 'email']
            )
        ]

    def validate_username(self, value):
        """Проверка имени пользователя."""
        if value.lower() == 'me':
            raise serializers.ValidationError(
                f'Имя {value} не может быть использованно')
        return value


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели CustomUserModels."""
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'date_joined')
        read_only_fields = ['password', 'confirmation_code']
        validators = [
            UniqueTogetherValidator(
                queryset=CustomUser.objects.all(),
                fields=['username', 'email']
            )
        ]

    def validate_username(self, value):
        """Проверка имени пользователя."""
        if value.lower() == 'me':
            raise serializers.ValidationError(
                f'Имя {value} не может быть использованно')
        return value


class CustomTokenSerializer(serializers.Serializer):
    """Получение токена."""
    username = serializers.CharField()
    confirmation_code = serializers.CharField()

    @classmethod
    def get_tokens_for_user(cls, user):
        """Обновление токена."""
        return RefreshToken.for_user(user)

    @staticmethod
    def validate_username(value):
        """Поиск указанных данных."""
        if not CustomUser.objects.filter(username=value).exists():
            raise NotFound(
                {'error': 'Не удается пройти аутентификацию с указанными '
                          f'учетными данными, проверьте username: {value}'}
            )
        return value

    def validate(self, attrs):
        """Проверка username и confirmation_code."""
        user = get_object_or_404(CustomUser, username=attrs['username'])
        if attrs['confirmation_code'] == user.confirmation_code:
            refresh = self.get_tokens_for_user(user)
            return {'token': str(refresh.access_token)}
        raise serializers.ValidationError('Данные не прошли проверку')


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
        fields = ('name', 'm_unit', 'id')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""
    class Meta:
        model = Tag
        fields = ('name', 'color', 'slug', 'id')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор списка ингредиентов в рецепте."""
    name = serializers.CharField(source='ingredient.name', read_only=True)
    m_unit = serializers.CharField(source='ingredient.m_unit', read_only=True)
    quantity = serializers.IntegerField(source='quantity')
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredients
        fields = ('name', 'measurement_unit', 'quantity', 'id')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалиализатор создания рецептов."""
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientsSerializer(
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
        for ingredient in ingredients:
            RecipeIngredients.objects.create(
                recipe=recipe,
                quantity=ingredient['quantity'],
                ingredient=ingredient['id']
            )
        return recipe

    def create(self, data):
        tags = data.pop('tags')
        image = data.pop('image')
        ingredients = data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **data)
        recipe.tags.set(tags)
        recipe.save()
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


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериалиализатор просмотра рецептов."""
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientsSerializer(
        read_only=True, many=True, source='ingredient_recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'ingredients', 'is_favorited',
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
