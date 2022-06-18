# Generated by Django 3.2.6 on 2022-06-18 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_rename_recipeingredients_recipeingredient'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='tag',
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(db_index=True, help_text='Выберите теги рецепта', related_name='recipes', to='recipes.Tag', verbose_name='Теги'),
        ),
    ]
