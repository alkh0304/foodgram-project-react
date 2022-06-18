from colorfield.fields import ColorField
from django.core import validators
from django.db import models

from users.models import CustomUser


class Ingredient(models.Model):
    name = models.CharField(max_length=256, verbose_name='Ингредиент')
    measurement_unit = models.CharField(
        max_length=256, verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=[
                'name',
                'measurement_unit'
            ], name='unique_ingredient'),
        ]

    def __str__(self):
        return f'{self.name} измеряются в {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Тег',
        unique=True
    )
    color = ColorField(
        max_length=8,
        default='#FF0000',
        unique=True,
        verbose_name='Цвет Тега')
    slug = models.SlugField(unique=True, verbose_name='Слаг Тега')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(fields=[
                'name',
                'slug'
            ], name='unique_tag'),
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название рецепта',
        unique=True
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение блюда'
    )
    text = models.TextField('Текст рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты, используемые в рецепте'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        db_index=True
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        help_text='Выберите теги рецепта',
        db_index=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        null=False,
        verbose_name='Время приготовления рецепта в минутах',
        validators=[validators.MinValueValidator(0)],
        default=30
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='ingredient_recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredient_recipe',
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Количество/объем ингредиента',
        validators=[validators.MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'
        ordering = ('recipe__name',)
        constraints = [
            models.UniqueConstraint(fields=[
                'ingredient',
                'recipe'
            ], name='unique_ingredient_amount'),
        ]

    def __str__(self):
        return (f'Для рецепта {self.recipe} необходимо {self.quantity} '
                f'ингредиента {self.ingredient}')


class ShoppingList(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='В списке у пользователя'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(fields=[
                'user',
                'recipe'
            ], name='unique_shopping_list'),
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в Список покупок'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='users_favorite',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=[
                'user',
                'recipe'
            ], name='unique_favorite'),
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в Избранное'
