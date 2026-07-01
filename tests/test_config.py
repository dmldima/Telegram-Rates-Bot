"""Consistency checks for configuration."""
from config import CURRENCY_ALIASES, SUPPORTED_PAIRS

VALID_CODES = {"USD", "EUR", "GBP", "CHF", "UAH", "PLN", "SGD"}


def test_alias_keys_are_lowercase():
    # normalize_code does a case-insensitive lookup via .lower(); keys must be
    # lowercase or they can never match.
    for key in CURRENCY_ALIASES:
        assert key == key.lower(), f"Alias key {key!r} is not lowercase"


def test_alias_values_are_known_codes():
    for value in CURRENCY_ALIASES.values():
        assert value in VALID_CODES, f"Alias points to unknown code {value!r}"


def test_no_self_referential_aliases():
    for key, value in CURRENCY_ALIASES.items():
        assert key.lower() != value.lower(), f"Redundant self-alias {key!r}"


def test_supported_pairs_use_known_codes():
    for pair in SUPPORTED_PAIRS:
        base, target = pair.split("/")
        assert base in VALID_CODES, f"Unknown base in {pair}"
        assert target in VALID_CODES, f"Unknown target in {pair}"
        assert base != target, f"Degenerate pair {pair}"
