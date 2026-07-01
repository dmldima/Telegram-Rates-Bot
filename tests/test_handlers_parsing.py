"""Tests for the message-parsing helpers in handlers."""
import pytest
from handlers import split_amount_and_date, sanitize_markdown, format_date_european


class TestSplitAmountAndDate:
    @pytest.mark.parametrize("text,amount,date_text", [
        ("100 21.04.2025", "100", "21.04.2025"),
        ("1000,50 today", "1000,50", "today"),
        ("1 000,50 yesterday", "1 000,50", "yesterday"),   # space thousands
        ("1.000,50 2025-04-21", "1.000,50", "2025-04-21"),
        ("100 2025-04-21", "100", "2025-04-21"),
    ])
    def test_amount_plus_date(self, text, amount, date_text):
        assert split_amount_and_date(text) == (amount, date_text)

    @pytest.mark.parametrize("text", [
        "today",
        "yesterday",
        "21.04.2025",
        "2 days ago",       # must NOT be read as amount=2
        "3 weeks ago",
        "100 days ago",     # relative date, not amount
    ])
    def test_date_only(self, text):
        amount, date_text = split_amount_and_date(text)
        assert amount is None
        assert date_text == text


class TestSanitizeMarkdown:
    @pytest.mark.parametrize("raw,expected", [
        ("John_Doe", "JohnDoe"),
        ("a*b`c[d", "abcd"),
        ("Normal Name", "Normal Name"),
    ])
    def test_strips_control_chars(self, raw, expected):
        assert sanitize_markdown(raw) == expected


class TestFormatDateEuropean:
    def test_iso_to_european(self):
        assert format_date_european("2025-04-21") == "21.04.2025"

    def test_non_iso_passthrough(self):
        assert format_date_european("weird") == "weird"
