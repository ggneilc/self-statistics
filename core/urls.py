from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "core"
urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("manifest.json", views.manifest_view, name="manifest"),
    path("sw.js", views.service_worker_view, name="service_worker"),
    path("dashboard/", views.dashboard_page, name="dashboard_page"),
    path("user/streak", views.get_current_streak, name="curr_streak"),
    path("wt/", views.workout_page, name="workout_page"),
    path("nutrition/", views.nutrition_page, name="nutrition_page"),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.HTMXLoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.HTMXLogoutView.as_view(next_page='core:home'), name='logout'),
    path("auth-modal/", views.auth_modal, name="auth_modal"),

    path("sleep/",      views.get_sleep, name="get_sleep"),
    path("sleep/edit",  views.edit_sleep, name="edit_sleep"),
    path("sleep/set",   views.add_sleep, name="add_sleep"),

    path("water/",      views.get_water, name="get_water"),
    path("water/add",   views.add_water, name="update_water"),

    path("bodyweight/", views.get_bodyweight, name="get_bw"),
    path("bodyweight/set", views.add_bodyweight, name="set_bw"),
    path("bodyweight/edit", views.edit_bodyweight, name="edit_bw"),

    path("profile/tz", views.update_timezone, name="set_tz"),
    path("profile/personal", views.info_setting, name="info_setting"),
    path("profile/theme", views.theme_setting, name="theme_setting"),
    path("profile/food", views.food_setting, name="food_setting"),
    path("profile/graphs", views.graph_setting, name="graph_setting"),
    path("profile/workout", views.workout_setting, name="workout_setting"),

    path("day/<str:date>", views.display_day, name="day"),
    path("today", views.display_today, name="today"),

    path("profile/", views.get_profile, name="profile"),
    path("back/", views.close_profile, name="close_profile"),

    path("delete/type/<int:w_type>", views.del_workout_type, name="del_type"),
    path("add/type", views.add_workout_type, name="addt"),
    path("edit/type/<int:type_id>", views.edit_workout_type, name="edit_type"),
]
