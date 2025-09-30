# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from calcounter.models import Food
from workouts.models import Workout, WorkoutType
from django.contrib.auth.models import User
from .models import Day, Profile
from django.db.models import Sum
from datetime import datetime


@receiver([post_save, post_delete], sender=Food)
def update_day_after_meal_change(sender, instance, **kwargs):
    signal = kwargs.get('signal')  # post_save or post_delete
    date = instance.day.date
    print(f"Updating {date}")
    day = instance.day

    # Check if food has 01-01-0001
    if (date == datetime(1, 1, 1)):
        print("flushing dead foods")
        # delete all foods that has 01-01-0001
        foods = Food.objects.filter(day=day)
        for f in foods:
            if not f.is_template:
                print(f"dead food found: {f}")
                instance.delete()
    else:
        total = Food.objects.filter(day=day).aggregate(
            total_cals=Sum('calories')
        )['total_cals'] or 0

        day.calories_consumed = total
        if signal == post_save:
            day.entered_meal = True
        day.save()


@receiver([post_save, post_delete], sender=Workout)
def update_day_after_workout_change(sender, instance, **kwargs):
    day = instance.day
    # did the user just delete or save
    exists = Workout.objects.filter(day=day).exists()
    print(f"found workout for day {day}: {exists}")
    day.did_workout = exists
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
                WorkoutType.objects.create(
                    name=name, user=instance, color=color)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
