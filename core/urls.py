from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "core"
urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.HTMXLoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.HTMXLogoutView.as_view(next_page='core:home'), name='logout'),
    path("auth-modal/", views.auth_modal, name="auth_modal"),
    path("profile/", views.get_profile, name="profile"),
    path("back/", views.close_profile, name="close_profile"),

    path("meal/", views.get_meal_column, name="get_meal"),
    path("lift/", views.get_lift_column, name="get_lift"),
    path("graphs/", views.get_graph_column, name="get_graph"),

    path("bodyweight/", views.get_bodyweight, name="get_bw"),
    path("profile/tz", views.update_timezone, name="set_tz"),
    path("bodyweight/set", views.add_bodyweight, name="set_bw"),
    path("day/<int:date>", views.display_day, name="day"),
    path("day/tasks", views.daily_goals, name="tasks"),
]
