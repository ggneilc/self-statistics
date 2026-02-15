from django.db import models
from django.conf import settings
from core.models import Day
from django.db.models import F, Sum

# Can add bodyweight & banded (support calisentics & women)
LIFT_TYPES = [
    ('M', 'Machine'),
    ('C', 'Cable'),
    ('B', 'Barbell'),
    ('D', 'Dumbbell')
]

BODYPARTS = [
    # Pull
    ('BI', 'Bicep'),
    ('TR', 'Trap'),
    ('LT', 'Lat'),
    ('RS', 'R. Delts'),
    ('FO', 'Forearms'),
    # Push
    ('CH', 'Chest'),
    ('TI', 'Tricep'),
    ('LS', 'L. Delts'),
    ('FS', 'F. Delts'),
    ('AB', 'Abs'),
    # Legs
    ('QD', 'Quadricep'),
    ('HM', 'Hamstring'),
    ('CV', 'Calf'),
    ('HP', 'Ab|Ads'),
    ('GL', 'Glutes'),
    # misc
]

bodypart_map = dict(BODYPARTS)


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
        return f"{self.name} ({self.user.username})"


class WorkoutTypeBodypart(models.Model):
    '''Links a WorkoutType to a specific muscle group code'''
    workout_type = models.ForeignKey(
        WorkoutType, on_delete=models.CASCADE, related_name='target_muscles'
    )
    bodypart = models.CharField(max_length=2, choices=BODYPARTS)

    class Meta:
        unique_together = ('workout_type', 'bodypart')

    def __str__(self):
        return f"{self.workout_type} - {self.bodypart}"

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
    
    def bodypart_list(self):
        codes = self.workout_type.target_muscles.values_list('bodypart', flat=True)
        return [(code, bodypart_map[code]) for code in codes if code in bodypart_map]


# Similar to Foods database : globally accessible to all users, stores static information
class MovementLibrary(models.Model):
    '''
        The 'Master' definition of an exercise. 
        Global Storage of all basic movements. 
        Stores both 'free' movements and 'premium' dlc packs
    '''
    name = models.CharField(max_length=100)
    bodypart = models.CharField(max_length=2, choices=BODYPARTS)
    secondary_bodypart = models.CharField(max_length=2, choices=BODYPARTS, blank=True, null=True)
    category = models.CharField(max_length=1, choices=LIFT_TYPES)
    is_premium = models.BooleanField(default=False)
    pack_name = models.CharField(max_length=50, blank=True, null=True) # e.g., "PPL Pack"
    
    def __str__(self):
        return f"{self.name} ({self.pack_name or 'Global'})"

# Similar to PantryItem : a movement the user is registering to themselves
class Movement(models.Model):
    '''
        A user's specific instance of a movement.
        Links back to the global library OR is a custom user creation.
    '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Link to global (null if they made a custom one)
    base_movement = models.ForeignKey(
        MovementLibrary, on_delete=models.SET_NULL, null=True, blank=True
    )
    # Override fields (for custom movement)
    name = models.CharField(max_length=100) 
    bodypart = models.CharField(max_length=2, choices=BODYPARTS)
    secondary_bodypart = models.CharField(max_length=2, choices=BODYPARTS, null=True, blank=True)
    category = models.CharField(max_length=1, choices=LIFT_TYPES)

    level = models.FloatField(default=1)
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.user} | {self.base_movement.name or self.name}"


class Lift(models.Model):
    '''
        Represents an instance of a movement performed
        - exercise_name
    '''
    movement = models.ForeignKey(Movement, on_delete=models.CASCADE, related_name='instances')
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='lifts')

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
        return f"{self.movement.name}: ({self.workout.workout_type} | {self.workout.day.date})"


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
        return f"{self.reps} reps @ {self.weight} ({self.lift.movement.name})"


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