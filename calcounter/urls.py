from django.urls import path

from . import views

app_name = "calcounter"
urlpatterns = [
    path("meal", views.meal_area, name="get_m"),
    path("food", views.food_area, name="get_f"),
    path("list/meal", views.list_meals, name="list_m"),
    path("list/food", views.list_foods, name="list_f"),
    path("list/meal/templates", views.list_meal_templates, name="templates_m"),
    path("list/food/templates", views.list_food_templates, name="templates_f"),

    path("add/food_to_meal/<int:fdc_id>",
         views.add_food_to_meal, name="add_food_to_meal"),
    path("food/button", views.get_food_input, name="food_input"),
    path("add/meal", views.add_meal, name="add"),
    path("add/meal/buttons", views.get_type_of_input, name="add_buttons"),
    path("add/meal/buttons/ingred", views.get_auto_buttons, name="auto_buttons"),
    path("add/meal/ingred/search", views.get_search_area, name="ingred_search"),
    path("add/food/search/", views.new_search_food, name="search_food"),
    path("add/food/complex/", views.new_complex_food, name="complex_food"),
    path("search/ingred/", views.query_ingredient, name="search_ingred"),
    path("search/ingred/<int:fdcId>",
         views.get_specific_usda_item, name="get_ingred"),
    path("add/<int:food_id>/", views.add_pantry_food, name="add_p"),
    path("edit/<int:food_id>/", views.edit_food, name="edit_food"),
    path("update/<int:food_id>/", views.update_food, name="update_food"),
    path("<int:food_id>/", views.render_food, name="render_food"),
    path("save/<int:food_id>/", views.save_template, name="save_template"),
    path("back/meal", views.cancel_form_m, name="cancel_m"),
    path("back/food", views.cancel_form_f, name="cancel_f"),
    path("delete/<int:food_id>/", views.delete_food, name="delete_food"),
    path("delete/template/<int:food_id>/",
         views.delete_food_template, name="delete_t"),
]
