import unittest
from unittest.mock import patch

from api.core.config import get_settings


class ConfigTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_normalizes_postgres_scheme_to_psycopg(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "DATABASE_URL": "postgres://user:pass@db-host:5432/training_lab",
                "APP_ENVIRONMENT": "staging",
            },
            clear=True,
        ):
            get_settings.cache_clear()
            settings = get_settings()

        self.assertEqual(
            settings.database_url,
            "postgresql+psycopg://user:pass@db-host:5432/training_lab",
        )
        self.assertEqual(settings.app_environment, "staging")

    def test_preserves_explicit_driver(self) -> None:
        with patch.dict(
            "os.environ",
            {"DATABASE_URL": "postgresql+psycopg://user:pass@db-host:5432/training_lab"},
            clear=True,
        ):
            get_settings.cache_clear()
            settings = get_settings()

        self.assertEqual(
            settings.database_url,
            "postgresql+psycopg://user:pass@db-host:5432/training_lab",
        )


if __name__ == "__main__":
    unittest.main()
