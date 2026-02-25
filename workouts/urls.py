from django.urls import path

from . import views

app_name = "workouts"
urlpatterns = [
     path("weekly/set/",   views.get_weekly_sets,   name="weekly_sets"),

     path("workouts/",        views.get_workouts,      name="workouts"),
     path("workouts/type/",   views.wtype_selection,   name="wtype_entry"),
     path("workouts/types/",   views.get_wtypes,   name="workout_types"),
     path("workouts/add/<int:wtype_id>/",    views.add_workout,       name="addw"),
     path("workouts/<int:workout_id>/", views.get_workout, name="get_workout"),
     path("workouts/<int:workout_id>/lifts/",
          views.get_lifts, name="workout_lifts/"),
     path("workouts/<int:workout_id>/delete/", views.delete_workout, name="delete_workout"),
     # adding movement 
     path("movement/add/",             views.add_movement, name="start"),
     path("movement/add/form",         views.add_movement, name="mv_form"),
     path("movement/add/<int:mv_id>",  views.add_movement, name="add_mv"),
     path("movement/add/custom",       views.add_movement, name="add_custom_mv"),
     # listing movements & filtering
     path("movements/",   views.get_movements,     name="movements"),
     path("movements/global/",      views.get_movements,  name="movements_global"),
     path("movements/active/",      views.get_movements,     name="movements_active"),
     path("movement/<int:movement_id>/", views.get_movement, name="movement"),
     # filter chips
     path("bodyparts/",   views.get_bodyparts,    name="bodyparts"),
     path("categories/active/",  views.get_categories,   name="categories_active"),
     path("categories/",  views.get_categories,   name="categories"),
     # active workout
     path("workout/add/lift/", views.add_lift, name="lift_selection"),
     path("workout/add/lift/<int:movement_id>/", views.add_lift, name="add_lift"),
     path("workout/add/set/<int:lift_id>/", views.add_set, name="add_set"),
     path("workout/edit/lift/<int:lift_id>/", views.edit_lift, name="edit_lift"),
     path("workout/edit/set/<int:set_id>/", views.edit_set, name="edit_set"),
     path("workout/delete/set/<int:set_id>/", views.delete_set, name="del_set"),
     path("workout/<int:workout_id>/end/", views.end_workout, name="end_workout"),
     path("workout/lift/<int:lift_id>/end/", views.end_lift, name="end_lift"),

     path("change/color/", views.change_color, name="change_color"),
     path("clear/", views.clear, name="clear"),
]