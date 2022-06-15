# Generated by Django 4.0.5 on 2022-06-15 00:52

import colorfield.fields
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FavoriteRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Избранное',
                'verbose_name_plural': 'Избранное',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='Ингредиент')),
                ('m_unit', models.CharField(max_length=256, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True, verbose_name='Название рецепта')),
                ('image', models.ImageField(upload_to='recipes/', verbose_name='Изображение блюда')),
                ('text', models.TextField(verbose_name='Текст рецепта')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации рецепта')),
                ('cooking_time', models.PositiveSmallIntegerField(default=30, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Время приготовления рецепта в минутах')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ('-pub_date',),
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredients',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Количество/объем ингредиента')),
            ],
            options={
                'verbose_name': 'Ингредиент для рецепта',
                'verbose_name_plural': 'Ингредиенты для рецепта',
                'ordering': ('recipe__name',),
            },
        ),
        migrations.CreateModel(
            name='ShoppingList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Список покупок',
                'verbose_name_plural': 'Список покупок',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True, verbose_name='Тег')),
                ('color', colorfield.fields.ColorField(default='#FF0000', image_field=None, max_length=8, samples=None, unique=True, verbose_name='Цвет Тега')),
                ('slug', models.SlugField(unique=True, verbose_name='Слаг Тега')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
            },
        ),
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(fields=('name', 'slug'), name='unique_tag'),
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_list', to='recipes.recipe', verbose_name='В списке у пользователя'),
        ),
    ]
