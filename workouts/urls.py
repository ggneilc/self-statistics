from django.urls import path

from . import views

app_name = "workouts"
urlpatterns = [
    path("entry/", views.get_workout_types, name="load_entry"),
    path("list/", views.get_workouts, name="list"),
    path("list/<int:workout_id>", views.get_lifts, name="listl"),
    path("get/wk/<int:workout_id>", views.get_workout_details, name="get_workout"),
    path("add/workout/<int:workout_type_id>", views.add_workout, name="addw"),

    path("overview/add/lift", views.get_workout_types, name="type_select"),
    path("overview/add/lift/bodypart/<int:workout_type_id>", 
         views.get_bodyparts, name="bp_selection"),
    path("overview/add/lift/machines",
         views.get_machines, name="machine_selection"),
    path("overview/add/lift/form",
         views.add_lift, name="get_lift_form"),
    path("overview/add/lift/form/submit",
         views.add_lift, name="submit_lift_form"),

    path("add/list/bodypart/<int:workout_type_id>/",
         views.get_bodyparts, name="bpb"),
    path("add/list/machines", views.get_machines, name="machines"),
    path("add/list/bp/mc/tmps", views.get_lift_templates, name="lift_templates"),
    path("add/lift", views.add_lift, name="addl"),
    path("get/lift/<int:lift_id>", views.get_lift_details, name="lift_details"),
    path("get/active/lifts/<int:workout_id>",
         views.get_active_lift_list, name="active_lifts"),
    path("add/lift/template/<int:lift_id>",
         views.add_lift_from_template, name="addlt"),
    path("add/lift/save/template/<int:lift_id>",
         views.add_lift_template, name="save_lift"),
    path("add/lift/<int:lift_id> ", views.add_set, name="adds"),
    path("edit/lift/<int:set_id> ", views.edit_set, name="edit_set"),
    path("edit/active/lift/<int:lift_id>",
         views.edit_active_workout_lift, name="edit_lift"),
    path("clear/lift/set ", views.clear, name="clear"),
    path("end/lift/<int:lift_id>", views.end_lift, name="end_l"),
    path("delete/wk/<int:workout_id>", views.del_workout, name="del_workout"),
    path("delete/set/<int:set_id>", views.delete_set, name="del_set"),
    path("cancel/", views.back, name="back"),
    path("end/", views.end_workout, name="endw"),
    path("change/color", views.change_color, name="change_color"),
    path("weekly_sets/", views.weekly_sets_dashboard, name="weekly_dash"),
    path("lift_overview/", views.lift_overview_dashboard, name="lift_dash"),
]
