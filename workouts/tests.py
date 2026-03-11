from django.test import TestCase
from django.contrib.auth.models import User
from workouts.models import (
    WorkoutType, WorkoutTypeBodypart, Movement, MovementLibrary,
    Lift, Set, Workout, WeeklyVolume,
)
from core.models import Day
from datetime import date


# ==============================================================================
# New user signal — default workout types & bodyparts
# ==============================================================================

class NewUserDefaultWorkoutTypesTest(TestCase):
    """Signal creates Push/Pull/Legs with the correct target muscle groups for every new user."""

    def setUp(self):
        self.user = User.objects.create_user('newguy', password='testpass')

    def test_three_default_types_created(self):
        types = WorkoutType.objects.filter(user=self.user)
        self.assertEqual(types.count(), 3)

    def test_default_type_names(self):
        names = set(WorkoutType.objects.filter(user=self.user).values_list('name', flat=True))
        self.assertEqual(names, {'Push', 'Pull', 'Legs'})

    def test_push_has_correct_bodyparts(self):
        push = WorkoutType.objects.get(user=self.user, name='Push')
        bodyparts = set(push.target_muscles.values_list('bodypart', flat=True))
        self.assertIn('CH', bodyparts)   # Chest
        self.assertIn('TI', bodyparts)   # Tricep
        self.assertIn('LS', bodyparts)   # Lateral Delts
        self.assertIn('FS', bodyparts)   # Front Delts
        self.assertIn('AB', bodyparts)   # Abs
        self.assertNotIn('BI', bodyparts)  # Bicep should NOT be in Push
        self.assertNotIn('LT', bodyparts)  # Lat should NOT be in Push

    def test_pull_has_correct_bodyparts(self):
        pull = WorkoutType.objects.get(user=self.user, name='Pull')
        bodyparts = set(pull.target_muscles.values_list('bodypart', flat=True))
        self.assertIn('BI', bodyparts)   # Bicep
        self.assertIn('LT', bodyparts)   # Lat
        self.assertIn('TR', bodyparts)   # Trap
        self.assertIn('RS', bodyparts)   # Rear Delts
        self.assertIn('FO', bodyparts)   # Forearms
        self.assertNotIn('CH', bodyparts)  # Chest should NOT be in Pull
        self.assertNotIn('QD', bodyparts)  # Quad should NOT be in Pull

    def test_legs_has_correct_bodyparts(self):
        legs = WorkoutType.objects.get(user=self.user, name='Legs')
        bodyparts = set(legs.target_muscles.values_list('bodypart', flat=True))
        self.assertIn('QD', bodyparts)   # Quad
        self.assertIn('HM', bodyparts)   # Hamstring
        self.assertIn('GL', bodyparts)   # Glutes
        self.assertIn('CV', bodyparts)   # Calf
        self.assertNotIn('CH', bodyparts)  # Chest should NOT be in Legs
        self.assertNotIn('BI', bodyparts)  # Bicep should NOT be in Legs

    def test_second_user_gets_own_independent_types(self):
        """Each user gets their own set of 3 types, not shared."""
        user2 = User.objects.create_user('otherguy', password='testpass')
        self.assertEqual(WorkoutType.objects.filter(user=self.user).count(), 3)
        self.assertEqual(WorkoutType.objects.filter(user=user2).count(), 3)
        # Total across both users = 6
        self.assertEqual(WorkoutType.objects.count(), 6)

    def test_bodypart_links_belong_to_correct_type(self):
        """WorkoutTypeBodypart records are linked to the correct WorkoutType."""
        push = WorkoutType.objects.get(user=self.user, name='Push')
        pull = WorkoutType.objects.get(user=self.user, name='Pull')
        # CH should only exist under Push, not Pull
        self.assertTrue(WorkoutTypeBodypart.objects.filter(workout_type=push, bodypart='CH').exists())
        self.assertFalse(WorkoutTypeBodypart.objects.filter(workout_type=pull, bodypart='CH').exists())


# ==============================================================================
# Movement uniqueness — same user cannot have two movements with the same name
# ==============================================================================

class MovementUniquenessTest(TestCase):
    """A user cannot have two movements with the same name (unique_together constraint)."""

    def setUp(self):
        self.user = User.objects.create_user('lifter', password='testpass')

    def test_duplicate_name_raises_error(self):
        Movement.objects.create(
            user=self.user, name='Bench Press', bodypart='CH', category='B'
        )
        with self.assertRaises(Exception):  # IntegrityError from unique_together
            Movement.objects.create(
                user=self.user, name='Bench Press', bodypart='CH', category='B'
            )

    def test_same_name_different_users_allowed(self):
        """Two different users can each have a movement named 'Bench Press'."""
        user2 = User.objects.create_user('lifter2', password='testpass')
        Movement.objects.create(
            user=self.user, name='Bench Press', bodypart='CH', category='B'
        )
        Movement.objects.create(
            user=user2, name='Bench Press', bodypart='CH', category='B'
        )
        self.assertEqual(Movement.objects.filter(name='Bench Press').count(), 2)

    def test_different_name_same_user_allowed(self):
        Movement.objects.create(
            user=self.user, name='Bench Press', bodypart='CH', category='B'
        )
        Movement.objects.create(
            user=self.user, name='Incline Press', bodypart='CH', category='B'
        )
        self.assertEqual(
            Movement.objects.filter(user=self.user, name__in=['Bench Press', 'Incline Press']).count(),
            2
        )

    def test_same_name_different_category_still_blocked(self):
        """Same name + same user is rejected even if category differs."""
        Movement.objects.create(
            user=self.user, name='Press', bodypart='CH', category='B'
        )
        with self.assertRaises(Exception):
            Movement.objects.create(
                user=self.user, name='Press', bodypart='LS', category='D'
            )


# ==============================================================================
# Movement deletion — cascades to lifts & sets; archive preserves history
# ==============================================================================

class MovementDeletionTest(TestCase):
    """Deleting a movement cascades to lifts/sets. Archiving preserves history."""

    def setUp(self):
        self.user = User.objects.create_user('athlete', password='testpass')
        self.push = WorkoutType.objects.get(user=self.user, name='Push')
        self.day = Day.objects.create(user=self.user, date=date(2025, 1, 10))
        self.workout = Workout.objects.create(
            day=self.day, workout_type=self.push, is_active=False
        )
        self.movement = Movement.objects.create(
            user=self.user, name='Bench Press', bodypart='CH', category='B'
        )
        self.lift = Lift.objects.create(movement=self.movement, workout=self.workout)
        Set.objects.create(lift=self.lift, reps=10, weight=135)
        Set.objects.create(lift=self.lift, reps=8, weight=145)

    def test_delete_movement_cascades_to_lift(self):
        lift_id = self.lift.id
        self.movement.delete()
        self.assertFalse(Lift.objects.filter(id=lift_id).exists())

    def test_delete_movement_cascades_to_sets(self):
        self.movement.delete()
        self.assertEqual(Set.objects.filter(lift__workout=self.workout).count(), 0)

    def test_workout_survives_movement_deletion(self):
        """The parent workout is not deleted when a movement is deleted."""
        self.movement.delete()
        self.assertTrue(Workout.objects.filter(id=self.workout.id).exists())

    def test_multiple_lifts_all_deleted_with_movement(self):
        """All lifts for a movement across different workouts are deleted."""
        day2 = Day.objects.create(user=self.user, date=date(2025, 1, 17))
        workout2 = Workout.objects.create(
            day=day2, workout_type=self.push, is_active=False
        )
        lift2 = Lift.objects.create(movement=self.movement, workout=workout2)
        Set.objects.create(lift=lift2, reps=5, weight=155)

        movement_id = self.movement.id
        self.movement.delete()
        self.assertFalse(Lift.objects.filter(movement_id=movement_id).exists())

    def test_archive_preserves_lifts_and_sets(self):
        """Archiving a movement keeps all historical lifts and sets intact."""
        self.movement.is_archived = True
        self.movement.save()
        self.assertTrue(Lift.objects.filter(id=self.lift.id).exists())
        self.assertEqual(Set.objects.filter(lift=self.lift).count(), 2)

    def test_archived_movement_excluded_from_active_list(self):
        """Archived movements are not returned in the active movement filter."""
        self.movement.is_archived = True
        self.movement.save()
        active = Movement.objects.filter(user=self.user, is_archived=False)
        self.assertNotIn(self.movement, active)

    def test_non_archived_movement_appears_in_active_list(self):
        active = Movement.objects.filter(user=self.user, is_archived=False)
        self.assertIn(self.movement, active)
