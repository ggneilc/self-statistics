from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Day, Profile
from datetime import date


# ==============================================================================
# Goal calculations — Harris-Benedict calorie & protein targets
# ==============================================================================

class MacroGoalCalculationTest(TestCase):
    """
    set_macro_goal signal computes calorie_goal and protein_goal for today's Day
    using yesterday's bodyweight and the user's profile (gender, height, age).

    Harris-Benedict (Male):
        BMR = 66.5 + (13.75 * bw_kg) + (5.003 * height_cm) - (6.75 * age)
        cals = BMR * 1.725
        protein = bodyweight_lbs * 0.8
    """

    def setUp(self):
        self.user = User.objects.create_user('fituser', password='testpass')
        # Signal auto-created Profile; update to known values
        self.user.profile.gender = 'M'
        self.user.profile.age = 25
        self.user.profile.height = 180.0  # cm
        self.user.profile.save()

    def _day(self, date_val, bodyweight=None):
        """Create or retrieve a Day, optionally setting bodyweight."""
        day, _ = Day.objects.get_or_create(user=self.user, date=date_val)
        if bodyweight is not None:
            day.bodyweight = bodyweight
            day.save()
        return day

    def _expected_male_cals(self, bw_lbs, height_cm, age):
        bw_kg = bw_lbs * 0.45359237
        BMR = 66.5 + (13.75 * bw_kg) + (5.003 * height_cm) - (6.75 * age)
        return BMR * 1.725

    # --- Happy path ---

    def test_male_calorie_goal_computed_correctly(self):
        """Calorie goal matches Harris-Benedict * 1.725 for known inputs."""
        self._day(date(2025, 1, 14), bodyweight=170)
        today = self._day(date(2025, 1, 15))
        today.refresh_from_db()

        expected = self._expected_male_cals(170, 180.0, 25)
        self.assertAlmostEqual(today.calorie_goal, expected, places=0)

    def test_protein_goal_is_08_times_bodyweight_lbs(self):
        """Protein goal = 0.8 * bodyweight in lbs."""
        self._day(date(2025, 1, 14), bodyweight=200)
        today = self._day(date(2025, 1, 15))
        today.refresh_from_db()
        self.assertAlmostEqual(today.protein_goal, 200 * 0.8, places=0)

    # --- No yesterday / missing data ---

    def test_no_yesterday_leaves_default_calorie_goal(self):
        """If no Day exists for yesterday, calorie_goal stays at default (2000)."""
        today = self._day(date(2025, 3, 1))
        today.refresh_from_db()
        self.assertEqual(today.calorie_goal, 2000)

    def test_no_yesterday_leaves_default_protein_goal(self):
        today = self._day(date(2025, 3, 1))
        today.refresh_from_db()
        self.assertEqual(today.protein_goal, 120)

    def test_yesterday_with_null_bodyweight_leaves_defaults(self):
        """Yesterday exists but has bodyweight=None: goals remain at defaults."""
        self._day(date(2025, 1, 14), bodyweight=None)
        today = self._day(date(2025, 1, 15))
        today.refresh_from_db()
        self.assertEqual(today.calorie_goal, 2000)

    # --- Changing bodyweight updates next day's goals ---

    def test_heavier_bodyweight_yields_higher_calorie_goal(self):
        """Increasing bodyweight increases the computed calorie goal."""
        self._day(date(2025, 2, 1), bodyweight=150)
        light_day = self._day(date(2025, 2, 2))
        light_day.refresh_from_db()
        cals_at_150 = light_day.calorie_goal

        # Update day 1 to heavier weight, re-trigger signal by saving day 2
        Day.objects.filter(user=self.user, date=date(2025, 2, 1)).update(bodyweight=200)
        light_day.notes = "re-trigger"
        light_day.save()
        light_day.refresh_from_db()

        self.assertGreater(light_day.calorie_goal, cals_at_150)

    def test_lighter_bodyweight_yields_lower_calorie_goal(self):
        """Decreasing bodyweight decreases the computed calorie goal."""
        self._day(date(2025, 2, 1), bodyweight=200)
        heavy_day = self._day(date(2025, 2, 2))
        heavy_day.refresh_from_db()
        cals_at_200 = heavy_day.calorie_goal

        Day.objects.filter(user=self.user, date=date(2025, 2, 1)).update(bodyweight=150)
        heavy_day.notes = "re-trigger"
        heavy_day.save()
        heavy_day.refresh_from_db()

        self.assertLess(heavy_day.calorie_goal, cals_at_200)

    def test_protein_goal_tracks_bodyweight_changes(self):
        """Protein goal updates when yesterday's bodyweight changes."""
        self._day(date(2025, 2, 1), bodyweight=170)
        today = self._day(date(2025, 2, 2))
        today.refresh_from_db()
        self.assertAlmostEqual(today.protein_goal, 170 * 0.8, places=0)

        Day.objects.filter(user=self.user, date=date(2025, 2, 1)).update(bodyweight=210)
        today.notes = "re-trigger"
        today.save()
        today.refresh_from_db()
        self.assertAlmostEqual(today.protein_goal, 210 * 0.8, places=0)

    # --- Profile attribute effects ---

    def test_older_user_has_lower_calorie_goal(self):
        """Age increases the subtracted term in BMR, so older users have lower calorie goals."""
        self._day(date(2025, 3, 1), bodyweight=170)
        today = self._day(date(2025, 3, 2))
        today.refresh_from_db()
        cals_age_25 = today.calorie_goal

        # Update profile to age 60
        self.user.profile.age = 60
        self.user.profile.save()
        today.notes = "re-trigger age 60"
        today.save()
        today.refresh_from_db()
        cals_age_60 = today.calorie_goal

        self.assertLess(cals_age_60, cals_age_25)

    def test_taller_user_has_higher_calorie_goal(self):
        """Height adds to BMR, so taller users have higher calorie goals."""
        self._day(date(2025, 4, 1), bodyweight=170)
        today = self._day(date(2025, 4, 2))
        today.refresh_from_db()
        cals_180cm = today.calorie_goal

        self.user.profile.height = 200.0
        self.user.profile.save()
        today.notes = "re-trigger height 200"
        today.save()
        today.refresh_from_db()
        cals_200cm = today.calorie_goal

        self.assertGreater(cals_200cm, cals_180cm)

    def test_goal_values_are_positive(self):
        """Calorie and protein goals should always be positive numbers."""
        self._day(date(2025, 5, 1), bodyweight=130)
        today = self._day(date(2025, 5, 2))
        today.refresh_from_db()
        self.assertGreater(today.calorie_goal, 0)
        self.assertGreater(today.protein_goal, 0)
