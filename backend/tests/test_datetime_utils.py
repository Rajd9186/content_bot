"""Tests for datetime_utils module."""

from datetime import datetime, timezone, timedelta

import pytest

from app.utils.datetime_utils import utc_now, utc_now_naive


class TestUtcNow:
    def test_returns_datetime(self):
        result = utc_now()
        assert isinstance(result, datetime)

    def test_is_timezone_aware(self):
        result = utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_is_close_to_now(self):
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after

    def test_returns_consistent_type(self):
        results = [utc_now() for _ in range(100)]
        assert all(r.tzinfo == timezone.utc for r in results)


class TestUtcNowNaive:
    def test_returns_datetime(self):
        result = utc_now_naive()
        assert isinstance(result, datetime)

    def test_is_timezone_naive(self):
        result = utc_now_naive()
        assert result.tzinfo is None

    def test_value_equals_utc(self):
        naive = utc_now_naive()
        aware = utc_now()
        # Allow 1s difference
        assert abs((naive - aware.replace(tzinfo=None)).total_seconds()) < 1.0


class TestTimezoneConsistency:
    def test_no_mixed_timezones_in_comparison(self):
        """utc_now() values should be directly comparable."""
        t1 = utc_now()
        t2 = utc_now()
        # This would raise TypeError if timezones were mixed
        diff = t2 - t1
        assert isinstance(diff, timedelta)

    def test_can_compare_with_database_values(self):
        """Simulate comparing with a DB column value."""
        db_value = datetime.now(timezone.utc)  # simulates what PostgreSQL returns
        app_value = utc_now()
        # No TypeError should occur
        assert (db_value < app_value) or (db_value >= app_value)
