from django.urls import path

from . import views

app_name = "calcounter"
urlpatterns = [
    path("list/", views.get_food, name="list"),
    path("list/template", views.get_food_templates, name="templates"),
    path("list/totals", views.calculate_totals, name="sum-nuts"),
    path("add/", views.add_food, name="add"),
    path("add/<int:food_id>/", views.add_food_template, name="add_t"),
    path("back/", views.cancel_form, name="back"),
    path("delete/<int:food_id>/", views.delete_food, name="delete_food"),
    path("delete/template/<int:food_id>/", views.delete_food_template, name="delete_t"),
]