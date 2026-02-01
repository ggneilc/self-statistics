from django.db import models
from django.conf import settings
import zoneinfo

RDA_LOOKUP = {
    'Minerals': {
    'sodium': {
        'Young Male': 1200,
        'Adult Male': 1500,
        'Young Female': 1200,
        'Adult Female': 1500
    },
    'potassium': {
        'Young Male': 2500,
        'Adult Male': 3400,
        'Young Female': 2300,
        'Adult Female': 2600
    },
    'calcium': {
        'Young Male': 1300,
        'Adult Male': 1000,
        'Young Female': 1300,
        'Adult Female': 1000
    },
    'magnesium': {
        'Young Male': 410,
        'Adult Male': 400,
        'Young Female': 360,
        'Adult Female': 320
    },
    'iron': {
        'Young Male': 11,
        'Adult Male': 8,
        'Young Female': 15,
        'Adult Female': 18
    },
    'zinc': {
        'Young Male': 8,
        'Adult Male': 11,
        'Young Female': 9,
        'Adult Female': 8
    }},
    'Vitamins': {
    'A': {
        'Young Male': 900,
        'Adult Male': 900,
        'Young Female': 900,
        'Adult Female': 700,
    },
    'B6': {
        'Young Male': 1.2,
        'Adult Male': 1.2,
        'Young Female': 1.2,
        'Adult Female': 1.2,
    },
    'B12': {
        'Young Male': 2.6,
        'Adult Male': 2.6,
        'Young Female': 2.6,
        'Adult Female': 2.6,
    },
    'C': {
        'Young Male': 75,
        'Adult Male': 90,
        'Young Female': 65,
        'Adult Female': 75,
    },
    'D': {
        'Young Male': 15,
        'Adult Male': 15,
        'Young Female': 15,
        'Adult Female': 15,
    },
    'E': {
        'Young Male': 15,
        'Adult Male': 15,
        'Young Female': 15,
        'Adult Female': 15,
    }}
}

class Profile(models.Model):
    GENDERS = [('M', 'Male'), ('F', 'Female')]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        choices=[(tz, tz) for tz in zoneinfo.available_timezones()]
    )

    height = models.FloatField(default=0)
    gender = models.CharField(
        max_length=1,
        choices=GENDERS,
        default='M',
    )
    age = models.IntegerField(default=18)
    weekly_set_goal = models.IntegerField(default=15)

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
    water_consumed = models.FloatField(default=0)
    calorie_goal = models.IntegerField(default=2000)
    protein_goal = models.IntegerField(default=120)
    water_goal = models.FloatField(default=50)
    sleep = models.FloatField(default=0)
    sleep_goal = models.FloatField(default=9)
    # protein_goal = Bodyweight !

    # task stuff -- unused
    did_workout = models.BooleanField(default=False)
    entered_meal = models.BooleanField(default=False)
    entered_bodyweight = models.BooleanField(default=False)

    # Graph stuff -- avg_x unused
    bodyweight = models.FloatField(null=True, blank=True)
    avg_calories = models.FloatField(null=True, blank=True)
    avg_protein = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ['-date']

    @property
    def macro_breakdown(self):
        '''
            returns (carbs, protein, fat) in grams
        '''
        protein_grams = self.protein_consumed
        protein_cals = protein_grams * 4
        fat_cals = (self.calories_consumed - protein_cals) * 0.3  # assume 30% from fat
        fat_grams = fat_cals / 9
        carb_cals = self.calories_consumed - (protein_cals + fat_cals)
        carb_grams = carb_cals / 4
        return (round(carb_grams), round(protein_grams), round(fat_grams))

    @property
    def mineral_breakdown(self):
        '''
            returns dict of mineral name to amount in mg
        '''
        minerals = {
            'zinc': 0,
            'magnesium': 0,
            'iron': 0,
            'calcium': 0,
            'potassium': 0,
            'sodium': 0,
        }
        for meal in self.meals.all():
            nutrients = meal.get_nutrients_consumed()
            minerals['sodium'] = minerals.get('sodium') + nutrients.get('sodium', 0)
            minerals['potassium'] = minerals.get('potassium') + nutrients.get('potassium', 0)
            minerals['calcium'] = minerals.get('calcium') + nutrients.get('calcium', 0)
            minerals['iron'] = minerals.get('iron') + nutrients.get('iron', 0)
            minerals['magnesium'] = minerals.get('magnesium') + nutrients.get('magnesium', 0)
            minerals['zinc'] = minerals.get('zinc') + nutrients.get('zinc', 0)
        return minerals

    @property
    def vitamin_breakdown(self):
        '''
            returns dict of vitamin name to amount in mg or mcg
        '''
        vitamins = {
            'A': 0,
            'B6': 0,
            'B12': 0,
            'C': 0,
            'D': 0,
            'E': 0,
        }
        for meal in self.meals.all():
            nutrients = meal.get_nutrients_consumed()
            vitamins['A'] = vitamins.get('A') + nutrients.get('vitamin_a', 0)
            vitamins['B6'] = vitamins.get('B6') + nutrients.get('vitamin_b6', 0)
            vitamins['B12'] = vitamins.get('B12') + nutrients.get('vitamin_b12', 0)
            vitamins['C'] = vitamins.get('C') + nutrients.get('vitamin_c', 0)
            vitamins['D'] = vitamins.get('D') + nutrients.get('vitamin_d', 0)
            vitamins['E'] = vitamins.get('E') + nutrients.get('vitamin_e', 0)
        return vitamins

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
