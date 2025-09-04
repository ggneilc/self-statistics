from django.urls import path

from . import views

app_name = "workouts"
urlpatterns = [
    path("list/", views.get_workouts, name="list"),
    path("list/<int:workout_id>", views.get_lifts, name="listl"),
    path("set/<int:workout_id>", views.set_workout_type, name="set_type"),
    path("delete/<int:workout_id>", views.del_workout, name="del_workout"),
    path("add/workout", views.add_workout, name="addw"),
    path("add/type", views.add_workout_type, name="addt"),
    path("entry/", views.load_workout_entry, name="load_entry"),
    path("end/", views.end_workout, name="endw"),
    path("add/lift", views.add_lift, name="addl"),
    path("change/color", views.change_color, name="change_color"),
]