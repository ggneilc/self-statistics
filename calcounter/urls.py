from django.urls import path

from . import views

app_name = "calcounter"
urlpatterns = [
    path("list/", views.get_food, name="list"),
    path("list/template", views.get_food_templates, name="templates"),
    path("list/totals", views.calculate_totals, name="sum-nuts"),
    path("add/", views.add_food, name="add"),
    path("add/<int:food_id>/", views.add_food_template, name="add_t"),
    path("edit/<int:food_id>/", views.edit_food, name="edit_food"),
    path("update/<int:food_id>/", views.update_food, name="update_food"),
    path("<int:food_id>/", views.render_food, name="render_food"),
    path("save/<int:food_id>/", views.save_template, name="save_template"),
    path("back/", views.cancel_form, name="back"),
    path("delete/<int:food_id>/", views.delete_food, name="delete_food"),
    path("delete/template/<int:food_id>/",
         views.delete_food_template, name="delete_t"),
]
