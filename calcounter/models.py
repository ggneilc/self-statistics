'''
 Meal : event of eating something
 Food : something that is eaten 
 MealConsumption : relationship model [food, serving]
 Ingredient : relationship model for complex food [food, serving]
'''
from django.db import models
from django.conf import settings
from django.db.models import Q
from core.models import Day

FRUIT_CLASSES = [
    'apple',
    'apples',
    'banana',
    'bananas',
    'orange',
    'oranges',
    'pear',
    'pears',
    'pineapple',
    'pineapples',
    'strawberry',
    'strawberries',
    'watermelon',
    'watermelons',
    'grape',
    'grapes',
    'kiwi',
    'kiwis',
    'mango',
    'mangos',
    'melon',
    'melons',
    'nectarine',
    'nectarines',
    'peach',
    'peaches',
    'plum',
    'plums',
    'raspberry',
    'raspberries',
]

VEGETABLE_CLASSES = [
    'lettuce',
    'lettuces',
    'spinach',
    'spinachs',
    'broccoli',
    'cauliflower',
    'carrot',
    'carrots',
    'tomato',
    'tomatoes',
    'onion',
    'onions',
    'garlic',
    'garlics',
    'pepper',
    'eggplant',
    'zucchini',
    'zucchinis',
    'squash',
    'pumpkin',
    'corn',
    'corns',
]

BEEF_CLASSES = [
    'beef',
    'beefs',
    'steak',
    'sirloin',
    'flank',
    'round',
    'chuck',
    'shoulder',
    'shortrib',
    'brisket',
]

NOODLE_CLASSES = [
    'noodle',
    'noodles',
    'barilla',
    'soba',
    'spaghetti',
    'thin spaghetti',
    'angel hair spaghetti',
    'rigatoni',
    'lasagna',
    'lasagna',
    'ravioli',
    'tortellini',
    'linguine',
    'macaroni',
    'pasta',
    'fettuccine',
    'farfalle',
    'capellini',
    'ramen',
    'ramen noodle',
    'ramen noodles',
]

CHICKEN_CLASSES = ['chicken', 'chickens']
RICE_CLASSES = ['rice', 'rices']
MILK_CLASSES = ['milk', 'milks']
CHEESE_CLASSES = ['cheese', 'cheeses']
EGGS_CLASSES = ['egg', 'eggs']
POTATO_CLASSES = ['potato', 'potatoes']
PORK_CLASSES = [
    'pork',
    'bacon',
    'ham',
    'sausage',
    'bologna',
    'salami',
    'pepperoni',
    'hot dog',
]

class FoodManager(models.Manager):
    def available_to_user(self, user):
        global_foods = models.Q(owner__isnull=True)
        user_foods = models.Q(owner=user)
        return self.filter(global_foods | user_foods)


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
    calcium = models.FloatField(blank=True, null=True)
    iron = models.FloatField(blank=True, null=True)
    magnesium = models.FloatField(blank=True, null=True)
    potassium = models.FloatField(blank=True, null=True)
    sodium = models.FloatField(blank=True, null=True)
    zinc = models.FloatField(blank=True, null=True)
    # Vitamins
    vitamin_a = models.FloatField(blank=True, null=True)
    vitamin_b6 = models.FloatField(blank=True, null=True)
    vitamin_b12 = models.FloatField(blank=True, null=True)
    vitamin_c = models.FloatField(blank=True, null=True)
    vitamin_d = models.FloatField(blank=True, null=True)
    vitamin_e = models.FloatField(blank=True, null=True)
    ingredients = models.ManyToManyField(
        'self',
        through='Ingredient',
        symmetrical=False,
        related_name='contained_in'
    )
    # Null = Global Food Item
    # Owner = Complex food item
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_foods'
    )
    is_active = models.BooleanField(default=True)

    objects = FoodManager()

    def __str__(self):
        return f"{self.name}: {self.calories}"

    def to_formatted_dict(self):
        """Returns the food item in the macros/minerals/vitamins structure."""
        # Define field mappings: { field_name: (Display Name, Unit) }
        MACRO_MAP = {
            'calories': ('Energy', 'kcal'), 'protein': ('Protein', 'g'),
            'fat': ('Total lipid (fat)', 'g'), 'carb': ('Carbohydrate, by difference', 'g'),
            'sugar': ('Sugars, total including NLEA', 'g'), 'fiber': ('Fiber, total dietary', 'g'),
            'cholesterol': ('Cholesterol', 'mg')
        }
        MINERAL_MAP = {
            'calcium': ('Calcium, Ca', 'mg'), 'iron': ('Iron, Fe', 'mg'),
            'magnesium': ('Magnesium, Mg', 'mg'), 'potassium': ('Potassium, K', 'mg'),
            'sodium': ('Sodium, Na', 'mg'), 'zinc': ('Zinc, Zn', 'mg')
        }
        VITAMIN_MAP = {
            'vitamin_a': ('Vitamin A, RAE', 'µg'), 'vitamin_b6': ('Vitamin B-6', 'mg'),
            'vitamin_b12': ('Vitamin B-12', 'µg'), 'vitamin_c': ('Vitamin C, total ascorbic acid', 'mg'),
            'vitamin_d': ('Vitamin D (D2 + D3)', 'µg'), 'vitamin_e': ('Vitamin E (alpha-tocopherol)', 'mg')
        }
        def group_fields(mapping):
            group = {}
            for field, (label, unit) in mapping.items():
                val = getattr(self, field)
                if val is not None:
                    group[label] = {"name": label, "value": val, "unit": unit}
            return group
        return {
            "fdc_id": self.fdc_id,
            "name": self.name,
            "macros": group_fields(MACRO_MAP),
            "minerals": group_fields(MINERAL_MAP),
            "vitamins": group_fields(VITAMIN_MAP)
        }

    @property
    def food_class(self):
        """
        Returns the food's class based on dominant macronutrient.
        One of: 'fat', 'protein', 'vegetable', 'sugar', 'starch'.
        For carb-dominant foods: if fiber dominates -> vegetable;
        otherwise sugar or starch by majority.
        """
        p = self.protein or 0
        f = self.fat or 0
        c = self.carb or 0
        sugar_g = self.sugar or 0
        fiber_g = self.fiber or 0
        starch_g = max(0, c - sugar_g - fiber_g)

        cal_p = p * 4
        cal_f = f * 9
        cal_c = c * 4

        # Food name is usda string:
        # 'Apple, raw, all parts'
        # 'Beef, rib, ...' 
        # 'Whole, Milk, ...'
        # need to classify by food name
        # branded foods have no commas
        if ',' in self.name:
            food_name = self.name.split(',')
        else:
            food_name = self.name.split(' ')
        for word in food_name:
            word = word.strip().lower()
            if word == 'spices':
                return 'spices'
            if word in FRUIT_CLASSES:
                return 'fruit'
            if word in VEGETABLE_CLASSES:
                return 'vegetable'
            if word in BEEF_CLASSES:
                return 'protein'
            if word in NOODLE_CLASSES:
                return 'noodle'
            if word in RICE_CLASSES:
                return 'rice'
            if word in MILK_CLASSES:
                return 'milk'
            if word in CHEESE_CLASSES:
                return 'cheese'
            if word in EGGS_CLASSES:
                return 'egg'
            if word in CHICKEN_CLASSES:
                return 'chicken'
            if word in POTATO_CLASSES:
                return 'potato'
            if word in PORK_CLASSES:
                return 'pork'
        if cal_p >= cal_f and cal_p >= cal_c:
            return 'protein'
        if cal_f >= cal_p and cal_f >= cal_c:
            return 'fat'
        # Carb dominant: classify by carb breakdown
        if fiber_g > 0 and fiber_g >= sugar_g and fiber_g >= starch_g:
            return 'fiber'
        if sugar_g >= starch_g:
            return 'sugar'
        return 'starch'

    @property
    def starch(self):
        """Starch in g per 100g (carb minus sugar and fiber)."""
        c, s, f = self.carb or 0, self.sugar or 0, self.fiber or 0
        return max(0, c - s - f)

    def get_badges(self):
        badges = []
        # Example: Protein is > 20% of total calories
        if self.protein and self.calories and (self.protein * 4 / self.calories) > 0.20:
            badges.append({'label': 'High Protein', 'icon': 'fa-dumbbell', 'color': '#d81b60'})
        
        # Example: Low Carb (less than 10g per 100g)
        if self.carb is not None and self.carb < 10:
            badges.append({'label': 'Low Carb', 'icon': 'fa-leaf', 'color': '#039be5'})
            
        # Example: High Volume (Low calorie density)
        if self.calories and self.calories < 100:
            badges.append({'label': 'High Volume', 'icon': 'fa-expand', 'color': '#43a047'})

        return badges

    def get_nutrition_consumed(self, serving_size):
        # Calculation: (Food's nutrient per 100g / 100) * serving_g
        # 'or 0' guards against None fields (nullable in DB)
        def scale(val): return ((val or 0) / 100) * serving_size
        calories = scale(self.calories)
        protein = scale(self.protein)
        fat = scale(self.fat)
        carb = scale(self.carb)
        sugar = scale(self.sugar)
        fiber = scale(self.fiber)
        cholesterol = scale(self.cholesterol)
        # Minerals
        calcium = scale(self.calcium)
        iron = scale(self.iron)
        magnesium = scale(self.magnesium)
        potassium = scale(self.potassium)
        sodium = scale(self.sodium)
        zinc = scale(self.zinc)
        # Vitamins
        vitamin_a = scale(self.vitamin_a)
        vitamin_b6 = scale(self.vitamin_b6)
        vitamin_b12 = scale(self.vitamin_b12)
        vitamin_c = scale(self.vitamin_c)
        vitamin_d = scale(self.vitamin_d)
        vitamin_e = scale(self.vitamin_e)
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
            'vitamin_e': vitamin_e,
        }


class FoodUnitManager(models.Manager):
    def accessible_to(self, user):
        return self.filter(Q(creator__isnull=True) | Q(creator=user))


class FoodUnit(models.Model):
    ''' 
    Maps a descriptive name to a gram weight for a specific food.
    This allows: "1 Medium Banana" -> 120g -> Nutrition Math.
    '''
    food = models.ForeignKey(
        Food, 
        on_delete=models.CASCADE, 
        related_name='units'
    )
    # The name the user sees (e.g., "cup", "slice", "large")
    name = models.CharField(max_length=50) 
    # The multiplier to get to grams (e.g., 15.0 for a tbsp)
    gram_weight = models.DecimalField(max_digits=10, decimal_places=2)
    # Useful for sorting the most common unit to the top of the list
    is_standard = models.BooleanField(
        default=False, 
        help_text="Is this a standard unit (like 'grams')?"
    )
    # Optional: Link to a user if you want them to have private 'baselines'
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    objects = FoodUnitManager()

    class Meta:
        # Prevents duplicate units for the same food (e.g., two "cups")
        unique_together = ('food', 'name', 'creator')

    def __str__(self):
        return f"{self.name}"


class Ingredient(models.Model):
    ''' Complex Food
     i.e. "mashed potato" is complex food
    'butter' is ingredient
    '2' is amount
    'tbsp' is unit
    '''
    complex_food = models.ForeignKey(Food, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Food, on_delete=models.CASCADE,
                                   related_name='is_ingredient_of')
    amount = models.FloatField()
    unit = models.ForeignKey(FoodUnit, on_delete=models.PROTECT, null=True)

    class Meta:
        unique_together = ('complex_food', 'ingredient')

    def __str__(self):
        return f"{self.complex_food.name} uses {self.amount} {self.unit.name} of {self.ingredient.name}"


class Meal(models.Model):
    '''
    'The Plate the user sees' 
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
    foods_consumed = models.ManyToManyField(
        Food,
        through='MealConsumption',
        related_name='consumed_in_meals'
    )

    def __str__(self):
        return f"Meal: {self.name or 'Unnamed'} on {self.day}"

    def get_nutrients_consumed(self):
        total_nutrients = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carb': 0,
            'sugar': 0,
            'fiber': 0,
            'cholesterol': 0,
            # Minerals
            'calcium': 0,
            'iron': 0,
            'magnesium': 0,
            'potassium': 0,
            'sodium': 0,
            'zinc': 0,
            # Vitamins
            'vitamin_a': 0,
            'vitamin_b6': 0,
            'vitamin_b12': 0,
            'vitamin_c': 0,
            'vitamin_d': 0,
            'vitamin_e': 0,
        }
        for item in self.items.prefetch_related('food', 'unit').all():
            if item.food:
                serving_size = item.amount * float(item.unit.gram_weight)
                nutrients = item.food.get_nutrition_consumed(serving_size)
                for key, value in nutrients.items():
                    total_nutrients[key] += value or 0
            else:  # Manual Input
                total_nutrients['calories'] += item.calories or 0
                total_nutrients['protein'] += item.protein or 0
                total_nutrients['fat'] += item.fat or 0
                total_nutrients['carb'] += item.carb or 0
                total_nutrients['sugar'] += item.sugar or 0
                total_nutrients['fiber'] += item.fiber or 0
                total_nutrients['cholesterol'] += item.cholesterol or 0
                # Minerals
                total_nutrients['calcium'] += item.calcium or 0
                total_nutrients['iron'] += item.iron or 0
                total_nutrients['magnesium'] += item.magnesium or 0
                total_nutrients['potassium'] += item.potassium or 0
                total_nutrients['sodium'] += item.sodium or 0
                total_nutrients['zinc'] += item.zinc or 0
                # Vitamins
                total_nutrients['vitamin_a'] += item.vitamin_a or 0
                total_nutrients['vitamin_b6'] += item.vitamin_b6 or 0
                total_nutrients['vitamin_b12'] += item.vitamin_b12 or 0
                total_nutrients['vitamin_c'] += item.vitamin_c or 0
                total_nutrients['vitamin_d'] += item.vitamin_d or 0
                total_nutrients['vitamin_e'] += item.vitamin_e or 0
        return total_nutrients


class MealConsumption(models.Model):
    '''
    'Each individual food on the plate'
    Food items and serving sizes consumed for a meal
    '''
    meal = models.ForeignKey(
        Meal, on_delete=models.CASCADE, related_name="items")
    food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True)
    amount = models.FloatField(null=True)
    unit = models.ForeignKey(FoodUnit, on_delete=models.PROTECT,null=True)

    # -- Manual Input Info --
    description = models.CharField(max_length=255, blank=True, null=True)
    # Macros
    calories = models.IntegerField(null=True)
    protein = models.IntegerField(null=True)
    fat = models.IntegerField(blank=True, null=True)
    carb = models.IntegerField(blank=True, null=True)
    sugar = models.IntegerField(blank=True, null=True)
    fiber = models.IntegerField(blank=True, null=True)
    cholesterol = models.IntegerField(blank=True, null=True)
    # Minerals
    calcium = models.FloatField(blank=True, null=True)
    iron = models.FloatField(blank=True, null=True)
    magnesium = models.FloatField(blank=True, null=True)
    potassium = models.FloatField(blank=True, null=True)
    sodium = models.FloatField(blank=True, null=True)
    zinc = models.FloatField(blank=True, null=True)
    # Vitamins
    vitamin_a = models.FloatField(blank=True, null=True)
    vitamin_b6 = models.FloatField(blank=True, null=True)
    vitamin_b12 = models.FloatField(blank=True, null=True)
    vitamin_c = models.FloatField(blank=True, null=True)
    vitamin_d = models.FloatField(blank=True, null=True)
    vitamin_e = models.FloatField(blank=True, null=True)

    def __str__(self):
        if self.food and self.unit:
            ret = f"{self.food.name} ({self.amount} {self.unit.name}) in {self.meal.name}"
        else:
            ret = f"Manual Input in {self.meal.name}"
        return ret
    def get_nutrition_consumed(self):
        # Calculation: (Food's nutrient per 100g / 100) * serving_g
        # serving_g = amount (in units) * gram_weight (grams per unit)
        serving_size = self.amount * float(self.unit.gram_weight)
        def scale(val): return ((val or 0) / 100) * serving_size
        calories = scale(self.food.calories)
        protein = scale(self.food.protein)
        fat = scale(self.food.fat)
        carb = scale(self.food.carb)
        sugar = scale(self.food.sugar)
        fiber = scale(self.food.fiber)
        cholesterol = scale(self.food.cholesterol)
        # Minerals
        calcium = scale(self.food.calcium)
        iron = scale(self.food.iron)
        magnesium = scale(self.food.magnesium)
        potassium = scale(self.food.potassium)
        sodium = scale(self.food.sodium)
        zinc = scale(self.food.zinc)
        # Vitamins
        vitamin_a = scale(self.food.vitamin_a)
        vitamin_b6 = scale(self.food.vitamin_b6)
        vitamin_b12 = scale(self.food.vitamin_b12)
        vitamin_c = scale(self.food.vitamin_c)
        vitamin_d = scale(self.food.vitamin_d)
        vitamin_e = scale(self.food.vitamin_e)
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
            'vitamin_e': vitamin_e,
        }


PANTRY_STATUS = [
    ("s", "IN STOCK"),
    ("l", "LOW STOCK"),
    ("o", "OUT OF STOCK")
]


class PantryItem(models.Model):
    ''' Food the user owns '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='pantry')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    # custom user defined name, defaults to food.name
    name = models.CharField(max_length=255, blank=True, null=True)
    amount = models.IntegerField(null=True, blank=True)
    unit = models.ForeignKey(FoodUnit, on_delete=models.PROTECT, null=True)
    status = models.CharField(max_length=1,
                              choices=PANTRY_STATUS,
                              default="o")
    is_template = models.BooleanField(default=False)


class Recipe(models.Model):
    ''' Instructions on creating a complex food (meal) '''
    # owner of recipe = food.owner (recipes exist only for complex foods)
    food = models.OneToOneField(Food, on_delete=models.PROTECT,
                                related_name="recipe", null=True)
    instructions = models.TextField(blank=True, null=True,
                                    help_text="Step by step instructions")
    prep_time = models.IntegerField(blank=True, null=True,
                                    help_text="in minutes")
    cook_time = models.IntegerField(blank=True, null=True,
                                   help_text="in minutes")

    def __str__(self):
        return f"Recipe for {self.food.name}"