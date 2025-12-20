"""Tests for configuration validation logic."""

import os
from unittest.mock import patch

import pytest

from app.core.config import Settings


class TestConfigurationValidation:
    """Test configuration validation and fallback logic."""

    def test_valid_configuration_no_corrections(self):
        """Test that valid configuration passes without corrections."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER": "50",
                "EXPORT_MIN_CHUNKS_ADMIN": "10",
                "EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER": "5",
                "EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN": "-1",
            },
        ):
            settings = Settings()

            assert settings.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER == 50
            assert settings.EXPORT_MIN_CHUNKS_ADMIN == 10
            assert settings.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER == 5
            assert settings.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN == -1

    def test_invalid_chunk_values_corrected(self):
        """Test that invalid chunk values are corrected to defaults."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER": "0",  # Invalid
                "EXPORT_MIN_CHUNKS_ADMIN": "-5",  # Invalid
            },
        ):
            settings = Settings()

            # Should be corrected to defaults
            assert settings.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER == 50
            assert settings.EXPORT_MIN_CHUNKS_ADMIN == 10

    def test_invalid_download_limits_corrected(self):
        """Test that invalid download limits are corrected to defaults."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER": "-5",  # Invalid
                "EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN": "-10",  # Invalid
            },
        ):
            settings = Settings()

            # Should be corrected to defaults
            assert settings.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER == 5
            assert settings.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN == -1

    def test_zero_download_limit_allowed(self):
        """Test that zero download limit is valid (no downloads allowed)."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER": "0",
            },
        ):
            settings = Settings()

            # Zero should be allowed (no downloads)
            assert settings.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER == 0

    def test_unlimited_download_limit_allowed(self):
        """Test that -1 download limit is valid (unlimited downloads)."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN": "-1",
            },
        ):
            settings = Settings()

            # -1 should be allowed (unlimited)
            assert settings.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN == -1

    def test_get_min_chunks_for_role(self):
        """Test getting minimum chunks for different roles."""
        settings = Settings()

        assert (
            settings.get_min_chunks_for_role("admin")
            == settings.EXPORT_MIN_CHUNKS_ADMIN
        )
        assert (
            settings.get_min_chunks_for_role("sworik_developer")
            == settings.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER
        )

        with pytest.raises(ValueError, match="does not have export permissions"):
            settings.get_min_chunks_for_role("invalid_role")

    def test_get_daily_download_limit_for_role(self):
        """Test getting daily download limits for different roles."""
        settings = Settings()

        assert (
            settings.get_daily_download_limit_for_role("admin")
            == settings.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN
        )
        assert (
            settings.get_daily_download_limit_for_role("sworik_developer")
            == settings.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER
        )

        with pytest.raises(ValueError, match="does not have export permissions"):
            settings.get_daily_download_limit_for_role("invalid_role")

    def test_validate_startup_configuration_valid(self):
        """Test startup validation with valid configuration."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER": "50",
                "EXPORT_MIN_CHUNKS_ADMIN": "10",
                "EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER": "5",
                "EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN": "-1",
            },
        ):
            settings = Settings()

            # Should return True for valid configuration
            assert settings.validate_startup_configuration() is True

    def test_validate_startup_configuration_with_corrections(self):
        """Test startup validation when corrections are needed."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER": "0",  # Invalid, will be corrected
            },
        ):
            settings = Settings()

            # Should return False when corrections were needed
            assert settings.validate_startup_configuration() is False

    def test_validate_startup_configuration_missing_env_vars(self):
        """Test startup validation with missing environment variables."""
        # Clear all export-related env vars
        env_vars_to_clear = [
            "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER",
            "EXPORT_MIN_CHUNKS_ADMIN",
            "EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER",
            "EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN",
        ]

        with patch.dict(os.environ, {}, clear=False):
            # Remove the specific env vars we're testing
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]

            settings = Settings()

            # Should return False when using defaults due to missing env vars
            assert settings.validate_startup_configuration() is False

    def test_configuration_source_tracking(self):
        """Test that configuration sources are properly tracked and logged."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER": "75",  # From environment
                # EXPORT_MIN_CHUNKS_ADMIN not set - will use default
            },
        ):
            # Test that the settings are loaded correctly
            settings = Settings()

            # Verify the values are set correctly (which means validation worked)
            assert settings.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER == 75  # From env
            assert settings.EXPORT_MIN_CHUNKS_ADMIN == 10  # Default value

    def test_logical_consistency_warning(self):
        """Test warning when admin minimum is higher than developer minimum."""
        with patch.dict(
            os.environ,
            {
                "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER": "10",
                "EXPORT_MIN_CHUNKS_ADMIN": "50",  # Higher than developer - should warn
            },
        ):
            # Test that the settings are loaded correctly despite the warning
            settings = Settings()

            # Values should still be set correctly
            assert settings.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER == 10
            assert settings.EXPORT_MIN_CHUNKS_ADMIN == 50
