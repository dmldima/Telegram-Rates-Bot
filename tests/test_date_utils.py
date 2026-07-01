"""Tests for date parsing."""
from datetime import date, timedelta
import pytest
from dateutil.relativedelta import relativedelta
from utils.date_utils import parse_date_any


class TestKeywords:
    def test_today(self):
        assert parse_date_any("today") == date.today().strftime("%Y-%m-%d")

    def test_yesterday(self):
        expected = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert parse_date_any("yesterday") == expected

    def test_localized_keywords(self):
        assert parse_date_any("сьогодні") == date.today().strftime("%Y-%m-%d")
        assert parse_date_any("вчора") == (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


class TestRelative:
    def test_days_ago(self):
        expected = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        assert parse_date_any("3 days ago") == expected

    def test_weeks_ago(self):
        expected = (date.today() - timedelta(weeks=2)).strftime("%Y-%m-%d")
        assert parse_date_any("2 weeks ago") == expected

    def test_months_ago_is_calendar_accurate(self):
        # Not a 30-day approximation.
        expected = (date.today() - relativedelta(months=2)).strftime("%Y-%m-%d")
        assert parse_date_any("2 months ago") == expected


class TestExplicitFormats:
    def test_european(self):
        assert parse_date_any("21.04.2025") == "2025-04-21"

    def test_iso(self):
        assert parse_date_any("2025-04-21") == "2025-04-21"

    def test_day_first_disambiguation(self):
        # 25 can't be a month -> day-first.
        assert parse_date_any("25.03.2024") == "2024-03-25"


class TestInvalid:
    @pytest.mark.parametrize("raw", ["", "   ", "not a date"])
    def test_invalid_raises(self, raw):
        with pytest.raises(ValueError):
            parse_date_any(raw)
