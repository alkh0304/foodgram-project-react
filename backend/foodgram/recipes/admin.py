from django.contrib import admin

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')


class IngredientInline(admin.TabularInline):
    model = Ingredient
    fields = ('name', 'measurement_unit')


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'name', 'color')
    list_filter = ('slug', 'name', 'color')
    search_fields = ('slug', 'name', 'color')


class TagInline(admin.TabularInline):
    model = Tag
    fields = ('slug', 'name', 'color')


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    inline = [IngredientInline, ]


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'pub_date', 'favorite_count')
    list_filter = ('name', 'author', 'pub_date', 'tags')
    search_fields = ('name', 'user__username')
    inline = [RecipeIngredientInline, TagInline]

    def favorite_count(self, obj):
        return obj.users_favorite.all().count()


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
admin.site.register(FavoriteRecipe, FavoriteRecipeAdmin)
