# Generated by Django 3.2.6 on 2022-06-16 21:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20220616_1156'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RecipeIngredients',
            new_name='RecipeIngredient',
        ),
    ]
