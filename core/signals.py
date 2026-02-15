from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.conf import settings
from .models import Day, Profile
from calcounter.models import MealConsumption
from workouts.models import Workout, WorkoutType, Set, WeeklyVolume, Movement, MovementLibrary
from datetime import datetime, timedelta


@receiver([post_save], sender=Day)
def set_macro_goal(sender, instance, created, **kwargs):
    # instance.date = YYYY-MM-DD
    user = instance.user
    today = instance.date

    # 1. Force conversion if 'today' is a string
    if isinstance(today, str):
        # Handles 'YYYY-MM-DD'
        today = datetime.strptime(today, '%Y-%m-%d').date()

    if (today == '0001-01-01'):
        return
    yesterday = today - timedelta(days=1)

    yesterday_obj = user.days.filter(date=yesterday).first()

    # if no bodyweight or day, just use default
    if not yesterday_obj:
        print("No yesterday found: cannot set goals")
        return
    bw = yesterday_obj.bodyweight
    if not bw:
        print("No bodyweight found: cannot set goals")
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


@receiver([post_save, post_delete], sender=MealConsumption)
def update_day_after_meal_change(sender, instance, **kwargs):
    # instance is a MealConsumption object
    meal = instance.meal
    day = meal.day
    print(f"Updating {day.date}")

    total_c, total_p = 0, 0

    for meal in day.meals.all():
        totals = meal.get_nutrients_consumed()
        total_c += totals['calories']
        total_p += totals['protein']

    print(f"New totals for {day.date}: {total_c} cals, {total_p} pro")
    Day.objects.filter(pk=day.id).update(
        calories_consumed = total_c,
        protein_consumed = total_p
    )


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



@receiver([post_save, post_delete], sender=Set)
def update_weekly_volume(sender, instance, **kwargs):
    # 1. Find the Sunday of the week this set belongs to
    workout_date = instance.lift.workout.day.date
    days_since_sunday = (workout_date.weekday() + 1) % 7
    sunday = workout_date - timedelta(days=days_since_sunday)
    
    user = instance.lift.workout.day.user
    bodypart = instance.lift.movement.bodypart

    # 2. Recalculate total sets for this specific user/week/muscle
    total_sets = Set.objects.filter(
        lift__workout__day__user=user,
        lift__workout__day__date__range=[sunday, sunday + timedelta(days=6)],
        lift__movement__bodypart=bodypart
    ).count()

    # 3. Update or create the volume record
    WeeklyVolume.objects.update_or_create(
        user=user,
        start_date=sunday,
        muscle_group=bodypart,
        defaults={'set_count': total_sets}
    )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def provision_starter_movements(sender, instance, created, **kwargs):
    if created:
        # Get the "Starter" movements from the Global Library
        # You can mark these in the DB with a specific flag or pack_name
        starter_blueprints = MovementLibrary.objects.filter(pack_name="Starter Pack")
        
        starter_movements = [
            Movement(
                user=instance,
                base_movement=bp,
                name=bp.name,
                bodypart=bp.bodypart,
                category=bp.category
            ) for bp in starter_blueprints
        ]
        
        Movement.objects.bulk_create(starter_movements)