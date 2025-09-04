import datetime
from django.db import models
from django.conf import settings


class Food(models.Model):
    ''' Basic Food Identity '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.TextField()
    calories = models.IntegerField(null=True)
    protein = models.IntegerField(null=True)
    fat = models.IntegerField(blank=True, null=True)
    carb = models.IntegerField(blank=True, null=True)

    date = models.DateField("Day Eaten")

    is_template = models.BooleanField(default=False)

    def was_eaten_today(self):
        return self.date == datetime.datetime.today().date()

    def __str__(self):
        return f"{self.name}: {self.calories}"