from django.db import models
from django.conf import settings


class WorkoutType(models.Model):
    '''
        User's defined workout types:
        - Push, pull, legs, arms, etc.
        - provides default of PPL
    '''
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_types')

    def __str__(self):
        return self.name


class Workout(models.Model):
    '''
        Represents an entire day of lifts
        - user
        - date
        - notes
        - is_active
        - lifts[]
    '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    workout_type = models.ForeignKey(WorkoutType, on_delete=models.PROTECT, null=True)

    date = models.DateField(auto_now_add=True)

    notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.workout_type} | {self.date}"

class Lift(models.Model):
    '''
        Represents a singular movement
        - Sets
        - Reps
        - Weight
        - RPE 
    '''
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='lifts')
    name = models.CharField(max_length=100)
    sets = models.IntegerField()
    reps = models.IntegerField()
    weight = models.FloatField()

    def __str__(self):
        return f"{self.name}: {self.sets}x{self.reps} @ {self.weight} lbs"