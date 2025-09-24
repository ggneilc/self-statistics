import datetime
from django.db import models
from core.models import Day


class Food(models.Model):
    ''' Basic Food Identity '''
    day = models.ForeignKey(Day, on_delete=models.CASCADE,
                            related_name="meals", null=True)
    name = models.TextField()
    # Macros
    calories = models.IntegerField(null=True)
    protein = models.IntegerField(null=True)
    fat = models.IntegerField(blank=True, null=True)
    carb = models.IntegerField(blank=True, null=True)
    # TODO: add Micronutrients

    is_template = models.BooleanField(default=False)

    def was_eaten_today(self):
        return self.date == datetime.datetime.today().date()

    def __str__(self):
        return f"{self.name}: {self.calories}"
