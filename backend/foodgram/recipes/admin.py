from django.contrib import admin
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredients, ShoppingList, Tag)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'm_unit')
    list_filter = ('name', 'm_unit')
    search_fields = ('name', 'm_unit')


class IngredientInline(admin.TabularInline):
    model = Ingredient
    fields = ('name', 'm_unit')


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'name', 'color')
    list_filter = ('slug', 'name', 'color')
    search_fields = ('slug', 'name', 'color')


class TagInline(admin.TabularInline):
    model = Tag
    fields = ('slug', 'name', 'color')


class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'quantity')
    search_fields = ('recipe__name', 'ingredient__name')
    inline = [IngredientInline, ]


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredients
    autocomplete_fields = ('ingredient',)


class RecipeAdmin(admin.ModelAdmin):
    def favorite_count(self, obj):
        return obj.users_favorite.all().count()

    list_display = ('id', 'name', 'author', 'pub_date', 'favorite_count')
    list_filter = ('name', 'author', 'pub_date', 'tag')
    search_fields = ('name', 'user__username')
    inline = [RecipeIngredientsInline, TagInline]


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(RecipeIngredients, RecipeIngredientsAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
admin.site.register(FavoriteRecipe, FavoriteRecipeAdmin)
