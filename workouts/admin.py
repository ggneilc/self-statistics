from django.contrib import admin

# Register your models here.
from .models import Workout, Lift, WorkoutType

admin.site.register(Workout)
admin.site.register(WorkoutType)
admin.site.register(Lift)