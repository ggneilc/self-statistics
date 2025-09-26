from django.db import models
from django.conf import settings
import pytz


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        choices=[(tz, tz) for tz in pytz.all_timezones]
    )

    def __str__(self):
        return f"{self.user.username} Profile"


class Day(models.Model):
    '''
        stored computations of day's stats
    '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name="days",
                             null=True)
    date = models.DateField()
    note = models.TextField(blank=True)

    # Goal Stuff
    calories_consumed = models.IntegerField(default=0)
    protein_consumed = models.IntegerField(default=0)
    calorie_goal = models.IntegerField(default=2000)
    # protein_goal = Bodyweight !

    # task stuff
    did_workout = models.BooleanField(default=False)
    entered_meal = models.BooleanField(default=False)
    entered_bodyweight = models.BooleanField(default=False)

    # Graph stuff
    bodyweight = models.FloatField(null=True, blank=True)
    avg_calories = models.FloatField(null=True, blank=True)
    avg_protein = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ['-date']

    @property
    def calorie_ratio(self):
        """
            produces 0.0 - 1.0 for heat map
        """
        return self.calories_consumed / self.calorie_goal if self.calorie_goal else 0

    @property
    def protein_ratio(self):
        return self.protein_consumed / self.bodyweight if self.bodyweight else 0

    def __str__(self):
        return f"{self.user.username} | {self.date}"
