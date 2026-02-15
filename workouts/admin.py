from django.contrib import admin

# Register your models here.
from .models import Workout, Lift, WorkoutType, Set, WeeklyVolume, MovementLibrary, Movement, WorkoutTypeBodypart

admin.site.register(Workout)
admin.site.register(WorkoutType)
admin.site.register(WorkoutTypeBodypart)
admin.site.register(Lift)
admin.site.register(Set)
admin.site.register(Movement)
admin.site.register(MovementLibrary)
admin.site.register(WeeklyVolume)