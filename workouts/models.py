from django.db import models
from django.conf import settings
from core.models import Day
from django.db.models import F, Sum


class WorkoutType(models.Model):
    '''
        User's defined workout types:
        - Push, pull, legs, arms, etc.
        - provides default of PPL
    '''
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workout_types')

    def __str__(self):
        return self.name


class Workout(models.Model):
    '''
        Represents an instance of going to the gym
        - user
        - date
        - is_active
        - lifts[]
        - start_time, end_time
        - soreness rating
        - notes
        - personal records
    '''
    day = models.ForeignKey(
        Day, on_delete=models.CASCADE, related_name="workouts")
    workout_type = models.ForeignKey(
        WorkoutType, on_delete=models.PROTECT, null=True)
    is_active = models.BooleanField(default=False)

    notes = models.TextField(blank=True)
    soreness = models.PositiveIntegerField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    personal_records = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.workout_type} | {self.day.date}"

    def total_volume(self):
        """
        Computes total volume lifted in this workout:
        sum of (weight * reps) across all sets of all lifts.
        """
        return (
            self.lifts
            .values('sets__weight', 'sets__reps')
            .aggregate(total=Sum(F('sets__weight') * F('sets__reps')))['total']
            or 0
        )


# Can add bodyweight & banded
LIFT_TYPES = [
    ('M', 'Machine'),
    ('C', 'Cable'),
    ('B', 'Barbell'),
    ('D', 'Dumbbell')]

BODYPARTS = [
    # Pull
    ('BI', 'Bicep'),
    ('TR', 'Trap'),
    ('LT', 'Lat'),
    # Push
    ('CH', 'Chest'),
    ('TI', 'Tricep'),
    ('SH', 'Shoulder'),
    # Legs
    ('QD', 'Quadricep'),
    ('HM', 'Hamstring'),
    ('CV', 'Calf'),
    ('HP', 'Ad/Abuctor'),
    ('GL', 'Glutes'),
    # misc
    ('AB', 'Abs'),
    ('FO', 'Forearms'),
]


class Lift(models.Model):
    '''
        Represents a movement performed, i.e. 'barbell bench press'
        - exercise_name
    '''
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='lifts',
        null=True,
        blank=True)
    # user for initial lift tracking 
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             null=True)
    exercise_name = models.CharField(max_length=100)
    is_template = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    lift_type = models.CharField(
        max_length=1,
        choices=LIFT_TYPES,
        null=True)
    bodypart = models.CharField(
        max_length=2,
        choices=BODYPARTS,
        null=True)

    @property
    def set_count(self):
        return self.sets.count()

    @property
    def total_reps(self):
        return self.sets.aggregate(Sum('reps'))['reps__sum'] or 0

    @property
    def total_volume(self):
        return self.sets.aggregate(
            total=Sum(F('reps') * F('weight'))
        )['total'] or 0

    def get_best_set(self):
        # Returns the set with the highest weight, or highest volume
        return self.sets.order_by('-weight', '-reps').first()

    def estimated_1rm(self):
        best = self.get_best_set()
        if best:
            # Brzycki Formula: Weight / (1.0278 - (0.0278 * Reps))
            return best.weight / (1.0278 - (0.0278 * best.reps))
        return 0

    def __str__(self):
        return f"{self.exercise_name}: ({self.workout.workout_type if self.workout else ''} - {self.workout.day.date if self.workout else ''})"


class Set(models.Model):
    '''
        Represent a set of a lift
        - reps 
        - weight
        - rir
        - rest
    '''
    lift = models.ForeignKey(
        Lift, on_delete=models.CASCADE, related_name="sets")
    order = models.PositiveIntegerField(default=0)
    reps = models.PositiveIntegerField()
    weight = models.FloatField(help_text="Weight used")
    rir = models.PositiveIntegerField(
        blank=True, null=True, help_text="Reps in reserve")
    rest = models.DurationField(
        blank=True, null=True, help_text="Rest time between sets")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.reps} reps @ {self.weight} ({self.lift.exercise_name})"


# Stored statistics of sets per muscle group per week
class WeeklyVolume(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    start_date = models.DateField() # Always the Sunday
    muscle_group = models.CharField(max_length=2, choices=BODYPARTS)
    set_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['user', 'start_date', 'muscle_group']