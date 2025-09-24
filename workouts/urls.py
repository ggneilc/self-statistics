from django.urls import path

from . import views

app_name = "workouts"
urlpatterns = [
    path("entry/", views.get_workout_types, name="load_entry"),
    path("list/", views.get_workouts, name="list"),
    path("list/<int:workout_id>", views.get_lifts, name="listl"),
    path("add/workout/<int:workout_type_id>", views.add_workout, name="addw"),
    path("add/type", views.add_workout_type, name="addt"),
    path("add/lift", views.add_lift, name="addl"),
    path("add/lift/<int:lift_id> ", views.add_set, name="adds"),
    path("end/lift/<int:lift_id>", views.end_lift, name="end_l"),
    path("delete/wk/<int:workout_id>", views.del_workout, name="del_workout"),
    path("delete/set/<int:set_id>", views.delete_set, name="del_set"),
    path("cancel/", views.back, name="back"),
    path("end/", views.end_workout, name="endw"),
    path("change/color", views.change_color, name="change_color"),
]
