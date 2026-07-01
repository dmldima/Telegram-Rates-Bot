"""Tests for currency-pair and amount validation."""
import pytest
from utils.validation import normalize_code, normalize_amount, validate_pair_text


class TestNormalizeCode:
    @pytest.mark.parametrize("raw,expected", [
        ("usd", "USD"),
        ("USD", "USD"),
        ("  eur ", "EUR"),
        ("gpb", "GBP"),      # common typo alias
        ("uds", "USD"),      # common typo alias
        ("eru", "EUR"),      # common typo alias
        ("dollar", "USD"),
        ("euro", "EUR"),
        ("pound", "GBP"),
        ("hryvnia", "UAH"),
        ("гривна", "UAH"),
        ("гривня", "UAH"),
        ("злотий", "PLN"),
        ("sgd", "SGD"),
    ])
    def test_aliases_and_codes(self, raw, expected):
        assert normalize_code(raw) == expected


class TestNormalizeAmount:
    @pytest.mark.parametrize("raw,expected", [
        ("100", 100.0),
        ("100.50", 100.5),
        ("100,50", 100.5),
        ("1,000.50", 1000.5),      # US format
        ("1.000,50", 1000.5),      # European format
        ("1 000,50", 1000.5),      # space thousands + comma decimal
        ("1 000.50", 1000.5),      # space thousands + dot decimal
        ("1'000.50", 1000.5),      # Swiss format
        ("1.234.567,89", 1234567.89),
        ("1,234,567.89", 1234567.89),
        ("1000", 1000.0),
    ])
    def test_formats(self, raw, expected):
        assert normalize_amount(raw) == pytest.approx(expected)

    @pytest.mark.parametrize("raw", ["", "   ", "abc", "1.2.3.x"])
    def test_invalid_raises(self, raw):
        with pytest.raises(ValueError):
            normalize_amount(raw)

    def test_negative_message_preserved(self):
        with pytest.raises(ValueError, match="negative"):
            normalize_amount("-5")

    def test_zero_message_preserved(self):
        with pytest.raises(ValueError, match="zero"):
            normalize_amount("0")


class TestValidatePairText:
    @pytest.mark.parametrize("raw,expected", [
        ("EUR/USD", ("EUR", "USD")),
        ("eur usd", ("EUR", "USD")),
        ("EUR-USD", ("EUR", "USD")),
        ("uah,usd", ("UAH", "USD")),
        ("USD/SGD", ("USD", "SGD")),
    ])
    def test_valid_pairs(self, raw, expected):
        assert validate_pair_text(raw) == expected

    def test_same_currency_rejected(self):
        with pytest.raises(ValueError, match="same"):
            validate_pair_text("USD/USD")

    def test_unsupported_pair_rejected(self):
        with pytest.raises(ValueError):
            validate_pair_text("USD/JPY")

    def test_empty_rejected(self):
        with pytest.raises(ValueError):
            validate_pair_text("")

    def test_single_code_rejected(self):
        with pytest.raises(ValueError):
            validate_pair_text("USD")
