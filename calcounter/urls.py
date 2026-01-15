from django.urls import path

from . import views

app_name = "calcounter"
urlpatterns = [
    path("meal", views.meal_area, name="get_m"),
    path("food", views.food_area, name="get_f"),
    path("list/meal", views.list_meals, name="list_m"),
    path("list/food/<str:action>", views.list_foods, name="list_f"),
    path("list/recipes", views.list_recipes, name="list_recipes"),
    path("list/meal/templates", views.list_meal_templates, name="templates_m"),
    path("list/food/templates", views.list_food_templates, name="templates_f"),

    path("food/button", views.get_food_input, name="food_input"),
    path("food/complex/ingred", views.add_ingredient_row, name="add_ingredient_row"),
    path("units-ingred", views.get_units_for_ingredient, name="get_units_for_ingredient"),
    path("add/recipe", views.new_recipe, name="add_recipe"),
    path("add/meal", views.add_meal, name="add"),
    path("add/meal/row", views.add_meal_row, name="add_meal_row"),
    path("add/meal/manualrow", views.add_manual_meal_row, name="add_manual_meal_row"),
    path("add/meal/buttons", views.get_type_of_input, name="add_buttons"),
    path("add/meal/buttons/ingred", views.get_auto_buttons, name="auto_buttons"),
    path("add/meal/ingred/search", views.get_search_area, name="ingred_search"),
    path("add/food/search/", views.new_search_food, name="search_food"),
    path("add/food/complex/", views.new_complex_food, name="complex_food"),
    path("search/ingred/", views.query_ingredient, name="search_ingred"),
    path("search/ingred/<int:fdcId>",
         views.get_specific_usda_item, name="get_ingred"),
    path("unit/<int:food_id>/", views.food_unit_modal, name="unit"),
    path("edit/unit/<int:unit_id>/", views.edit_unit, name="edit_unit"),
    path("edit/unit-return/<int:unit_id>/", views.get_unit, name="get_unit"),
    path("add/<int:food_id>/", views.add_pantry_food, name="add_p"),
    path("update/<int:item_id>/<str:action>", views.update_pantry_item, name="update_pantry"),
    path("update/recipe/<int:recipe_id>", views.update_recipe, name="edit_recipe"),

    path("<int:food_id>/", views.render_food, name="render_food"),
    path("save/<int:food_id>/", views.save_template, name="save_template"),
    path("back/meal", views.cancel_form_m, name="cancel_m"),
    path("back/food", views.cancel_form_f, name="cancel_f"),
    path("delete/f/<int:pantry_id>", views.delete_food, name="delete_food"),
    path("delete/m/<int:meal_id>", views.delete_meal, name="delete_meal"),
    path("delete/r/<int:recipe_id>", views.delete_recipe, name="delete_recipe"),
    path("delete/u/<int:unit_id>", views.delete_unit, name="delete_unit"),
     path("clear/", views.clear, name="clear"),
]
