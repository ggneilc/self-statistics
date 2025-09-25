from django.db import models
from django.conf import settings
from core.models import Day


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


class Lift(models.Model):
    '''
        Represents a movement performed, i.e. 'barbell bench press'
        - exercise_name
    '''
    workout = models.ForeignKey(
        Workout, on_delete=models.CASCADE, related_name='lifts')
    exercise_name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.exercise_name}: ({self.workout.workout_type} - {self.workout.day.date})"


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
