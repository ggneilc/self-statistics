from django.db import models
from core.models import Day


class Food(models.Model):
    '''
    Static Composition of a 100g Substance Consumed:
    1. Simple Foundational Food Item (USDA, Nutrition Label)
    2. Complex Food Item (Mashed Potato, Marinara Sauce)
    '''
    name = models.CharField(max_length=255, blank=True, null=True)
    fdc_id = models.CharField(max_length=20, blank=True, null=True)
    # -- nutrients per 100g --
    # Macros
    calories = models.IntegerField(null=True)
    protein = models.IntegerField(null=True)
    fat = models.IntegerField(blank=True, null=True)
    carb = models.IntegerField(blank=True, null=True)
    sugar = models.IntegerField(blank=True, null=True)
    fiber = models.IntegerField(blank=True, null=True)
    cholesterol = models.IntegerField(blank=True, null=True)
    # Minerals
    calcium = models.IntegerField(blank=True, null=True)
    iron = models.IntegerField(blank=True, null=True)
    magnesium = models.IntegerField(blank=True, null=True)
    postassium = models.IntegerField(blank=True, null=True)
    sodium = models.IntegerField(blank=True, null=True)
    zinc = models.IntegerField(blank=True, null=True)
    # Vitamins
    vitamin_a = models.IntegerField(blank=True, null=True)
    vitamin_b6 = models.IntegerField(blank=True, null=True)
    vitamin_b12 = models.IntegerField(blank=True, null=True)
    vitamin_c = models.IntegerField(blank=True, null=True)
    vitamin_d = models.IntegerField(blank=True, null=True)
    vitamin_e = models.IntegerField(blank=True, null=True)

    is_template = models.BooleanField(default=False)

    ingredients = models.ManyToManyField(
        'self',
        through='IngredientComposition',
        symmetrical=False,
        related_name='used_in_foods'
    )

    def __str__(self):
        return f"{self.name}: {self.calories}"

    def get_nutrition_consumed(self, serving_size):
        # Calculation: (Food's nutrient per 100g / 100) * serving_g
        calories = (self.calories / 100) * serving_size
        protein = (self.protein / 100) * serving_size
        fat = (self.fat / 100) * serving_size
        carb = (self.carb / 100) * serving_size
        sugar = (self.sugar / 100) * serving_size
        fiber = (self.fiber / 100) * serving_size
        cholesterol = (self.cholesterol / 100) * serving_size
        # Minerals
        calcium = (self.calcium / 100) * serving_size
        iron = (self.iron / 100) * serving_size
        magnesium = (self.magnesium / 100) * serving_size
        potassium = (self.potassium / 100) * serving_size
        sodium = (self.sodium / 100) * serving_size
        zinc = (self.zinc / 100) * serving_size
        # Vitamins
        vitamin_a = (self.vitamin_a / 100) * serving_size
        vitamin_b6 = (self.vitamin_b6 / 100) * serving_size
        vitamin_b12 = (self.vitamin_b12 / 100) * serving_size
        vitamin_c = (self.vitamin_c / 100) * serving_size
        vitamin_d = (self.vitamin_d / 100) * serving_size
        vitamin_e = (self.vitamin_e / 100) * serving_size

        return {
            'calories': calories,
            'protein': protein,
            'fat': fat,
            'carb': carb,
            'sugar': sugar,
            'fiber': fiber,
            'cholesterol': cholesterol,
            # Minerals
            'calcium': calcium,
            'iron': iron,
            'magnesium': magnesium,
            'potassium': potassium,
            'sodium': sodium,
            'zinc': zinc,
            # Vitamins
            'vitamin_a': vitamin_a,
            'vitamin_b6': vitamin_b6,
            'vitamin_b12': vitamin_b12,
            'vitamin_c': vitamin_c,
            'vitamin_d': vitamin_d,
            'vitamin_e ': vitamin_e,
        }


class Meal(models.Model):
    '''
    Specific Food(s) Eaten on a day:
    - day: Day occured
    - foods[]: Food eaten
    - serving_size[]: amount in units
    - unit[]: oz, g, lb
    @get_macros(): standardize (food[i] x serving_size[i]) to g
    '''
    day = models.ForeignKey(Day, on_delete=models.CASCADE,
                            related_name="meals", null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    is_template = models.BooleanField(default=False)
    foods_consumed = models.ManytoManyField(
        Food,
        through='MealConsumption',
        related_name='consumed_in_meals'
    )

    def __str__(self):
        return f"Meal: {self.name or 'Unnamed'} on {self.date_consumed.date()}"


class IngredientComposition(models.Model):
    ''' Complex Food
     i.e. "mashed potato" is component of meal which
    '''
    complex_food = models.ForeignKey(Food, on_delete=models.CASCADE,
                                     related_name='components')
    ingredient = models.ForeignKey(Food, on_delete=models.CASCADE,
                                   related_name='is_ingredient_of')
    quantity_g = models.FloatField()

    class Meta:
        unique_together = ('complex_food', 'ingredient')

    def __str__(self):
        return f"{self.complex_food.name} uses {self.quantity_g}g of {self.ingredient.name}"


class MealConsumption(models.Model):
    '''
    Food items and serving sizes consumed for a meal
    '''
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)

    serving_g = models.FloatField()

    class Meta:
        unique_together = ('meal', 'food')

    def __str__(self):
        return f"{self.food.name} ({self.serving_g}g) in {self.meal.name}"

    def get_nutrition_consumed(self):
        # Calculation: (Food's nutrient per 100g / 100) * serving_g
        calories = (self.food.calories / 100) * self.serving_g
        protein = (self.food.protein / 100) * self.serving_g
        fat = (self.food.fat / 100) * self.serving_g
        carb = (self.food.carb / 100) * self.serving_g
        sugar = (self.food.sugar / 100) * self.serving_g
        fiber = (self.food.fiber / 100) * self.serving_g
        cholesterol = (self.food.cholesterol / 100) * self.serving_g
        # Minerals
        calcium = (self.food.calcium / 100) * self.serving_g
        iron = (self.food.iron / 100) * self.serving_g
        magnesium = (self.food.magnesium / 100) * self.serving_g
        potassium = (self.food.potassium / 100) * self.serving_g
        sodium = (self.food.sodium / 100) * self.serving_g
        zinc = (self.food.zinc / 100) * self.serving_g
        # Vitamins
        vitamin_a = (self.food.vitamin_a / 100) * self.serving_g
        vitamin_b6 = (self.food.vitamin_b6 / 100) * self.serving_g
        vitamin_b12 = (self.food.vitamin_b12 / 100) * self.serving_g
        vitamin_c = (self.food.vitamin_c / 100) * self.serving_g
        vitamin_d = (self.food.vitamin_d / 100) * self.serving_g
        vitamin_e = (self.food.vitamin_e / 100) * self.serving_g

        return {
            'calories': calories,
            'protein': protein,
            'fat': fat,
            'carb': carb,
            'sugar': sugar,
            'fiber': fiber,
            'cholesterol': cholesterol,
            # Minerals
            'calcium': calcium,
            'iron': iron,
            'magnesium': magnesium,
            'potassium': potassium,
            'sodium': sodium,
            'zinc': zinc,
            # Vitamins
            'vitamin_a': vitamin_a,
            'vitamin_b6': vitamin_b6,
            'vitamin_b12': vitamin_b12,
            'vitamin_c': vitamin_c,
            'vitamin_d': vitamin_d,
            'vitamin_e ': vitamin_e,
        }


class Recipe(models.Model):
    ''' Instructions on Food Entity '''
    food = models.OneToOneField(Food, on_delete=models.PROTECT,
                                related_name="recipe", null=True)
    name = models.TextField()
