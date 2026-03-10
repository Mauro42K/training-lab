import math
import unittest
import uuid

from api.core.config import Settings
from api.services.trimp_engine import TrimpEngineService
from api.services.trimp_profile_resolver import TrimpPhysiologyProfile


class StaticProfileResolver:
    def __init__(self, profile: TrimpPhysiologyProfile) -> None:
        self.profile = profile

    def resolve_for_user(self, *, user_id):
        _ = user_id
        return self.profile


def make_settings() -> Settings:
    return Settings(
        database_url=None,
        app_environment="test",
        training_lab_api_key=None,
        ingest_max_batch_size=500,
        trimp_active_model_version=1,
        trimp_active_method="banister_hrr",
        trimp_hr_rest_default=60,
        trimp_hr_max_default=190,
        trimp_sport_factor_run=1.0,
        trimp_sport_factor_bike=0.75,
        trimp_sport_factor_strength=0.35,
        trimp_sport_factor_walk=0.25,
        trimp_timezone_fallback="America/New_York",
    )


class TrimpEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = make_settings()
        self.user_id = uuid.uuid4()
        self.profile = TrimpPhysiologyProfile(hr_rest_bpm=60, hr_max_bpm=190, source="user_profile")
        self.service = TrimpEngineService(
            settings=self.settings,
            profile_resolver=StaticProfileResolver(self.profile),
        )

    def test_with_hr_uses_banister_hrr(self) -> None:
        result = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="run",
            duration_sec=3600,
            avg_hr_bpm=150,
        )
        hrr = (150 - 60) / (190 - 60)
        expected = 60.0 * hrr * (0.64 * math.exp(1.92 * hrr))
        self.assertAlmostEqual(result.trimp_value, expected, places=9)
        self.assertEqual(result.trimp_source, "real")
        self.assertEqual(result.trimp_method, "banister_hrr")
        self.assertEqual(result.trimp_model_version, 1)
        self.assertEqual(result.hr_rest_bpm_used, 60)
        self.assertEqual(result.hr_max_bpm_used, 190)
        self.assertIsNone(result.intensity_factor_used)
        self.assertTrue(result.is_computed)
        self.assertFalse(result.is_excluded)

    def test_without_hr_uses_sport_factor(self) -> None:
        result = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="bike",
            duration_sec=3600,
            avg_hr_bpm=None,
        )
        self.assertAlmostEqual(result.trimp_value, 45.0, places=9)
        self.assertEqual(result.trimp_source, "estimated")
        self.assertEqual(result.intensity_factor_used, 0.75)
        self.assertTrue(result.is_computed)
        self.assertFalse(result.is_excluded)

    def test_clamps_hrr_to_zero_when_avg_hr_below_rest(self) -> None:
        result = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="run",
            duration_sec=3600,
            avg_hr_bpm=50,
        )
        self.assertAlmostEqual(result.trimp_value, 0.0, places=9)
        self.assertEqual(result.trimp_source, "real")

    def test_clamps_hrr_to_one_when_avg_hr_above_max(self) -> None:
        result = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="run",
            duration_sec=3600,
            avg_hr_bpm=220,
        )
        expected = 60.0 * 1.0 * (0.64 * math.exp(1.92))
        self.assertAlmostEqual(result.trimp_value, expected, places=9)
        self.assertEqual(result.trimp_source, "real")

    def test_duration_zero_returns_zero(self) -> None:
        result = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="strength",
            duration_sec=0,
            avg_hr_bpm=None,
        )
        self.assertEqual(result.trimp_value, 0.0)
        self.assertEqual(result.trimp_source, "estimated")

    def test_other_sport_returns_excluded_result(self) -> None:
        result = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="other",
            duration_sec=1800,
            avg_hr_bpm=140,
        )
        self.assertEqual(result.trimp_value, 0.0)
        self.assertEqual(result.trimp_source, "excluded")
        self.assertFalse(result.is_computed)
        self.assertTrue(result.is_excluded)
        self.assertIsNone(result.hr_rest_bpm_used)
        self.assertIsNone(result.hr_max_bpm_used)
        self.assertIsNone(result.intensity_factor_used)

    def test_deterministic_output_for_same_input(self) -> None:
        first = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="run",
            duration_sec=2700,
            avg_hr_bpm=145,
        )
        second = self.service.calculate_for_workout(
            user_id=self.user_id,
            sport="run",
            duration_sec=2700,
            avg_hr_bpm=145,
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
