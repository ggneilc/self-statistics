from django.contrib import admin

from .models import Food, FoodUnit, PantryItem, Meal, MealConsumption, Ingredient, Recipe
# Register your models here.

admin.site.register(Food)
admin.site.register(FoodUnit)
admin.site.register(PantryItem)
admin.site.register(Meal)
admin.site.register(MealConsumption)
admin.site.register(Ingredient)
admin.site.register(Recipe)