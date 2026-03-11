from django.test import TestCase
from django.contrib.auth.models import User
from calcounter.models import Food, FoodUnit, Ingredient, Meal, MealConsumption
from core.models import Day
from datetime import date


# ==============================================================================
# Food.get_nutrition_consumed() — per-100g scaling via unit gram_weight
# ==============================================================================

class FoodNutritionScalingTest(TestCase):
    """Food.get_nutrition_consumed(serving_size) correctly scales per-100g values."""

    def setUp(self):
        self.food = Food.objects.create(
            name="Chicken Breast",
            calories=165, protein=31, fat=4, carb=0,
            sodium=74.0, calcium=15.0,
        )
        self.cup_unit = FoodUnit.objects.create(
            food=self.food, name="cup", gram_weight=140.0
        )

    def test_100g_returns_base_values(self):
        result = self.food.get_nutrition_consumed(100)
        self.assertAlmostEqual(result['calories'], 165.0)
        self.assertAlmostEqual(result['protein'], 31.0)
        self.assertAlmostEqual(result['fat'], 4.0)
        self.assertAlmostEqual(result['carb'], 0.0)

    def test_custom_unit_scales_correctly(self):
        """1 cup (140g) should return 140% of per-100g values."""
        serving_g = 1 * float(self.cup_unit.gram_weight)
        result = self.food.get_nutrition_consumed(serving_g)
        self.assertAlmostEqual(result['calories'], 165 * 1.4)
        self.assertAlmostEqual(result['protein'], 31 * 1.4)
        self.assertAlmostEqual(result['sodium'], 74.0 * 1.4)

    def test_fractional_serving_scales_correctly(self):
        """0.5 cups (70g) should return half the 140g values."""
        serving_g = 0.5 * float(self.cup_unit.gram_weight)
        result = self.food.get_nutrition_consumed(serving_g)
        self.assertAlmostEqual(result['calories'], 165 * 0.7)
        self.assertAlmostEqual(result['protein'], 31 * 0.7)

    def test_zero_serving_returns_zeros(self):
        result = self.food.get_nutrition_consumed(0)
        self.assertEqual(result['calories'], 0)
        self.assertEqual(result['protein'], 0)

    def test_null_nutrient_fields_treated_as_zero(self):
        """None fields (minerals, vitamins not set) must not crash and return 0."""
        sparse = Food.objects.create(name="Sparse", calories=100, protein=5)
        result = sparse.get_nutrition_consumed(200)
        self.assertAlmostEqual(result['calories'], 200.0)
        self.assertAlmostEqual(result['protein'], 10.0)
        self.assertEqual(result['fat'], 0)
        self.assertEqual(result['calcium'], 0)
        self.assertEqual(result['vitamin_c'], 0)

    def test_large_serving_scales_proportionally(self):
        """10000g serving returns 100x the per-100g values without error."""
        result = self.food.get_nutrition_consumed(10000)
        self.assertAlmostEqual(result['calories'], 165 * 100)


# ==============================================================================
# MealConsumption.get_nutrition_consumed() — unit-aware scaling
# ==============================================================================

class MealConsumptionNutritionTest(TestCase):
    """MealConsumption.get_nutrition_consumed() uses unit.gram_weight to scale food nutrients."""

    def setUp(self):
        self.user = User.objects.create_user('alice', password='testpass')
        self.food = Food.objects.create(
            name="Whole Milk",
            calories=61, protein=3, fat=3, carb=5, calcium=113.0,
        )
        self.cup_unit = FoodUnit.objects.create(
            food=self.food, name="cup", gram_weight=244.0
        )
        self.tbsp_unit = FoodUnit.objects.create(
            food=self.food, name="tablespoon", gram_weight=15.0
        )
        self.day = Day.objects.create(user=self.user, date=date(2025, 1, 15))
        self.meal = Meal.objects.create(day=self.day, name="Breakfast")

    def test_one_cup_calories(self):
        """1 cup (244g): 61/100 * 244 = 148.84 kcal."""
        mc = MealConsumption.objects.create(
            meal=self.meal, food=self.food, amount=1.0, unit=self.cup_unit
        )
        result = mc.get_nutrition_consumed()
        self.assertAlmostEqual(result['calories'], 148.84, places=1)

    def test_two_cups_is_double_one_cup(self):
        mc1 = MealConsumption(meal=self.meal, food=self.food, amount=1.0, unit=self.cup_unit)
        mc2 = MealConsumption(meal=self.meal, food=self.food, amount=2.0, unit=self.cup_unit)
        r1 = mc1.get_nutrition_consumed()
        r2 = mc2.get_nutrition_consumed()
        self.assertAlmostEqual(r2['calories'], r1['calories'] * 2)
        self.assertAlmostEqual(r2['calcium'], r1['calcium'] * 2)

    def test_tablespoon_unit_scales_correctly(self):
        """2 tablespoons (30g): 61/100 * 30 = 18.3 kcal."""
        mc = MealConsumption.objects.create(
            meal=self.meal, food=self.food, amount=2.0, unit=self.tbsp_unit
        )
        result = mc.get_nutrition_consumed()
        self.assertAlmostEqual(result['calories'], 18.3, places=1)

    def test_calcium_scales_with_unit(self):
        """Minerals scale the same way as macros via gram_weight."""
        mc = MealConsumption.objects.create(
            meal=self.meal, food=self.food, amount=1.0, unit=self.cup_unit
        )
        result = mc.get_nutrition_consumed()
        expected_calcium = 113.0 / 100 * 244.0
        self.assertAlmostEqual(result['calcium'], expected_calcium, places=1)


# ==============================================================================
# Meal.get_nutrients_consumed() — aggregation across all MealConsumption items
# ==============================================================================

class MealAggregateNutritionTest(TestCase):
    """Meal.get_nutrients_consumed() correctly sums nutrients across all items."""

    def setUp(self):
        self.user = User.objects.create_user('bob', password='testpass')
        self.day = Day.objects.create(user=self.user, date=date(2025, 1, 15))
        self.meal = Meal.objects.create(day=self.day, name="Lunch")

        self.rice = Food.objects.create(
            name="White Rice", calories=130, protein=3, fat=0, carb=28
        )
        self.chicken = Food.objects.create(
            name="Chicken", calories=165, protein=31, fat=4, carb=0
        )
        self.rice_unit = FoodUnit.objects.create(
            food=self.rice, name="cup", gram_weight=186.0
        )
        self.chicken_unit = FoodUnit.objects.create(
            food=self.chicken, name="oz", gram_weight=28.35
        )

    def test_empty_meal_returns_all_zeros(self):
        result = self.meal.get_nutrients_consumed()
        self.assertEqual(result['calories'], 0)
        self.assertEqual(result['protein'], 0)
        self.assertEqual(result['fat'], 0)

    def test_single_food_returns_scaled_nutrients(self):
        """1 cup of rice (186g): 130/100 * 186 = 241.8 kcal."""
        MealConsumption.objects.create(
            meal=self.meal, food=self.rice, amount=1.0, unit=self.rice_unit
        )
        result = self.meal.get_nutrients_consumed()
        self.assertAlmostEqual(result['calories'], 241.8, places=1)

    def test_multiple_foods_sum_correctly(self):
        MealConsumption.objects.create(
            meal=self.meal, food=self.rice, amount=1.0, unit=self.rice_unit
        )
        MealConsumption.objects.create(
            meal=self.meal, food=self.chicken, amount=4.0, unit=self.chicken_unit
        )
        result = self.meal.get_nutrients_consumed()
        rice_cals = 130 / 100 * 186
        chicken_cals = 165 / 100 * (4 * 28.35)
        self.assertAlmostEqual(result['calories'], rice_cals + chicken_cals, places=0)

        rice_protein = 3 / 100 * 186
        chicken_protein = 31 / 100 * (4 * 28.35)
        self.assertAlmostEqual(result['protein'], rice_protein + chicken_protein, places=0)

    def test_fat_and_carbs_summed_across_foods(self):
        MealConsumption.objects.create(
            meal=self.meal, food=self.rice, amount=1.0, unit=self.rice_unit
        )
        MealConsumption.objects.create(
            meal=self.meal, food=self.chicken, amount=4.0, unit=self.chicken_unit
        )
        result = self.meal.get_nutrients_consumed()
        expected_carb = 28 / 100 * 186  # only rice has carbs
        expected_fat = 4 / 100 * (4 * 28.35)  # only chicken has fat
        self.assertAlmostEqual(result['carb'], expected_carb, places=1)
        self.assertAlmostEqual(result['fat'], expected_fat, places=1)


# ==============================================================================
# Complex Food via custom units
# ==============================================================================

class ComplexFoodConsumptionTest(TestCase):
    """A complex food consumed via a custom serving unit scales its stored per-100g values."""

    def setUp(self):
        self.user = User.objects.create_user('carol', password='testpass')
        self.day = Day.objects.create(user=self.user, date=date(2025, 2, 1))
        self.meal = Meal.objects.create(day=self.day, name="Dinner")

        self.butter = Food.objects.create(
            name="Butter", calories=717, protein=1, fat=81, carb=0
        )
        self.potato = Food.objects.create(
            name="Potato", calories=77, protein=2, fat=0, carb=17
        )
        self.tbsp_unit = FoodUnit.objects.create(
            food=self.butter, name="tbsp", gram_weight=14.0
        )
        self.gram_unit = FoodUnit.objects.create(
            food=self.potato, name="grams", gram_weight=1.0
        )
        # Complex food with its own pre-computed per-100g macros
        self.mashed = Food.objects.create(
            name="Mashed Potato", owner=self.user,
            calories=113, protein=2, fat=5, carb=17,
        )
        self.scoop_unit = FoodUnit.objects.create(
            food=self.mashed, name="scoop", gram_weight=200.0
        )
        Ingredient.objects.create(
            complex_food=self.mashed, ingredient=self.butter,
            amount=2, unit=self.tbsp_unit
        )
        Ingredient.objects.create(
            complex_food=self.mashed, ingredient=self.potato,
            amount=300, unit=self.gram_unit
        )

    def test_one_scoop_doubles_per_100g_values(self):
        """1 scoop (200g) = 2× the per-100g values stored on the complex food."""
        MealConsumption.objects.create(
            meal=self.meal, food=self.mashed, amount=1.0, unit=self.scoop_unit
        )
        result = self.meal.get_nutrients_consumed()
        self.assertAlmostEqual(result['calories'], 226.0, places=1)  # 113 * 2
        self.assertAlmostEqual(result['fat'], 10.0, places=1)        # 5 * 2

    def test_half_scoop_returns_base_100g_values(self):
        """0.5 scoops (100g) returns the exact per-100g stored values."""
        MealConsumption.objects.create(
            meal=self.meal, food=self.mashed, amount=0.5, unit=self.scoop_unit
        )
        result = self.meal.get_nutrients_consumed()
        self.assertAlmostEqual(result['calories'], 113.0, places=1)
        self.assertAlmostEqual(result['protein'], 2.0, places=1)

    def test_complex_food_mixed_with_simple_food_sums_correctly(self):
        simple = Food.objects.create(name="Apple", calories=52, protein=0, fat=0, carb=14)
        apple_unit = FoodUnit.objects.create(food=simple, name="medium", gram_weight=182.0)
        MealConsumption.objects.create(
            meal=self.meal, food=self.mashed, amount=1.0, unit=self.scoop_unit
        )
        MealConsumption.objects.create(
            meal=self.meal, food=simple, amount=1.0, unit=apple_unit
        )
        result = self.meal.get_nutrients_consumed()
        mashed_cals = 113 / 100 * 200
        apple_cals = 52 / 100 * 182
        self.assertAlmostEqual(result['calories'], mashed_cals + apple_cals, places=0)


# ==============================================================================
# Food.to_formatted_dict() — USDA-style nutrient structure parsing
# ==============================================================================

class FoodFormattedDictTest(TestCase):
    """Food.to_formatted_dict() returns the correct USDA-style structure and values."""

    def setUp(self):
        self.food = Food.objects.create(
            name="Whole Milk, 3.25% milkfat",
            fdc_id="1097512",
            calories=61, protein=3, fat=3, carb=5,
            calcium=113.0, potassium=150.0,
            vitamin_a=46.0, vitamin_d=1.3,
        )

    def test_returns_required_top_level_keys(self):
        result = self.food.to_formatted_dict()
        for key in ('fdc_id', 'name', 'macros', 'minerals', 'vitamins'):
            self.assertIn(key, result)

    def test_fdc_id_and_name_correct(self):
        result = self.food.to_formatted_dict()
        self.assertEqual(result['fdc_id'], "1097512")
        self.assertEqual(result['name'], "Whole Milk, 3.25% milkfat")

    def test_macro_energy_value_and_unit(self):
        result = self.food.to_formatted_dict()
        energy = result['macros']['Energy']
        self.assertEqual(energy['value'], 61)
        self.assertEqual(energy['unit'], 'kcal')

    def test_null_fields_excluded_from_output(self):
        """Fields that are None (e.g. fiber not set) should not appear in the dict."""
        result = self.food.to_formatted_dict()
        self.assertNotIn('Fiber, total dietary', result['macros'])
        self.assertNotIn('Zinc, Zn', result['minerals'])

    def test_mineral_value_correct(self):
        result = self.food.to_formatted_dict()
        self.assertIn('Calcium, Ca', result['minerals'])
        self.assertEqual(result['minerals']['Calcium, Ca']['value'], 113.0)

    def test_vitamin_d_value_and_unit(self):
        result = self.food.to_formatted_dict()
        vit_d = result['vitamins']['Vitamin D (D2 + D3)']
        self.assertEqual(vit_d['value'], 1.3)
        self.assertEqual(vit_d['unit'], 'µg')

    def test_get_nutrition_consumed_matches_formatted_dict_at_100g(self):
        """At 100g serving, get_nutrition_consumed should match to_formatted_dict values."""
        nutrition = self.food.get_nutrition_consumed(100)
        formatted = self.food.to_formatted_dict()
        self.assertAlmostEqual(nutrition['calories'], formatted['macros']['Energy']['value'])
        self.assertAlmostEqual(nutrition['calcium'], formatted['minerals']['Calcium, Ca']['value'])
