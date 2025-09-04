# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from calcounter.models import Food
from workouts.models import Workout, WorkoutType
from django.contrib.auth.models import User
from .models import Day
from django.db.models import Sum
from datetime import datetime

@receiver([post_save, post_delete], sender=Food)
def update_day_after_meal_change(sender, instance, **kwargs):
    user = instance.user
    date = instance.date
    print(instance.date)

    day, _ = Day.objects.get_or_create(user=user, date=date)

    # Check if food has 01-01-0001
    if (date == datetime(1,1,1)):
        print("flushing dead foods")
        # delete all foods that has 01-01-0001
        _ = Food.objects.filter(user=user, date=date).delete()
        instance.delete()
        # delete the day
        day.delete()
    else:
        total = Food.objects.filter(user=user, date=date).aggregate(
            total_cals=Sum('calories')
        )['total_cals'] or 0

        day.calories_consumed = total
        day.save()



@receiver([post_save, post_delete], sender=Workout)
def update_day_after_workout_change(sender, instance, **kwargs):
    user = instance.user
    date = instance.date

    day, _ = Day.objects.get_or_create(user=user, date=date)
    exists = Workout.objects.filter(user=user, date=date).exists()
    day.workout_done = exists
    day.save()

DEFAULT_TYPES = [
    ("Push", "#66ff66"),
    ("Pull", "#ff6666"),
    ("Legs", "#66ccff"),
]

@receiver(post_save, sender=User)
def create_default_workout_types(sender, instance, created, **kwargs):
    if created:
        if not WorkoutType.objects.filter(user=instance).exists():
            for name, color in DEFAULT_TYPES:
                WorkoutType.objects.create(name=name, user=instance, color=color)