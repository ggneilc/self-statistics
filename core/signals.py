# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from calcounter.models import Food
from workouts.models import Workout, WorkoutType
from django.contrib.auth.models import User
from .models import Day, Profile
from django.db.models import Sum
from datetime import datetime, timedelta


@receiver([post_save], sender=Day)
def set_macro_goal(sender, instance, created, **kwargs):
    # instance.date = YYYY-MM-DD
    user = instance.user
    today = instance.date
    if (today == '0001-01-01'):
        return
    yesterday = today - timedelta(days=1)

    yesterday_obj = user.days.filter(date=yesterday).first()

    # if no bodyweight or day, just use default
    if not yesterday_obj:
        return
    bw = yesterday_obj.bodyweight
    if not bw:
        return

    print(f"Setting macros for {instance.date} for user {user}:")
    # Calories determined with Harris-Benedict
    if user.profile.gender == "M":
        bw_kg = bw * 0.45359237
        BMR = 66.5 + (13.75 * bw_kg) + (5.003 *
                                        user.profile.height) - (6.75 * user.profile.age)
        cals = BMR * 1.725
        pro = bw * 0.8
    elif user.profile.gender == "W":
        bw_kg = bw * 0.45359237
        BMR = 655.1 + (9.563 * bw_kg) + (1.850 *
                                         user.profile.height) - (4.676 * user.profile.age)
        cals = BMR * 1.725
        pro = bw * 0.8

    print(f"{cals=}, {pro=}")
    Day.objects.filter(pk=instance.pk).update(
        calorie_goal=cals,
        protein_goal=pro
    )


# @receiver([post_save, post_delete], sender=Food)
# def update_day_after_meal_change(sender, instance, **kwargs):
#    signal = kwargs.get('signal')  # post_save or post_delete
#    date = instance.day.date
#    print(f"Updating {date}")
#    day = instance.day

    # Check if food has 01-01-0001
#    if (date == datetime(1, 1, 1)):
#        print("flushing dead foods")
    # delete all foods that has 01-01-0001
#        foods = Food.objects.filter(day=day)
#        for f in foods:
#            if not f.is_template:
#                print(f"dead food found: {f}")
#                instance.delete()
#    else:
#        total_c = Food.objects.filter(day=day).aggregate(
#            total_cals=Sum('calories')
#        )['total_cals'] or 0
#        total_p = Food.objects.filter(day=day).aggregate(
#            total_pro=Sum('protein')
#        )['total_pro'] or 0
#
#        Day.objects.filter(pk=day.id).update(
#            calories_consumed = total_c,
#            protein_consumed = total_p
#        )


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
