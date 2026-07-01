"""
Configuration module for Currency Rate Bot.
Contains supported pairs, aliases, and API settings.
"""
import os
from typing import Final

# API Configuration
# Primary source for major currency pairs.
FRANKFURTER_BASE_URL: Final[str] = "https://api.frankfurter.app"
# Primary source for UAH pairs (National Bank of Ukraine).
NBU_BASE_URL: Final[str] = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
# Backup source for major currencies (latest rates only — no history).
EXCHANGERATE_API_URL: Final[str] = "https://api.exchangerate-api.com/v4/latest"

# Fallback behavior
USE_FALLBACK_DATE: Final[bool] = True
MAX_FALLBACK_DAYS: Final[int] = 7

# HTTP Settings
REQUEST_TIMEOUT: Final[int] = 10
MAX_RETRIES: Final[int] = 3
RETRY_DELAY: Final[float] = 1.0

# Bot Settings
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
PORT: int = int(os.getenv("PORT", "8080"))

# Redis Configuration
REDIS_URL: str = os.getenv("REDIS_URL", "")
USE_REDIS: bool = bool(REDIS_URL)

# Supported currency pairs
SUPPORTED_PAIRS: Final[set[str]] = {
    # Major pairs
    "EUR/USD", "EUR/GBP", "EUR/CHF", 
    "USD/EUR", "USD/GBP", "USD/CHF", 
    "EUR/SGD", "USD/SGD",
    # UAH pairs (UAH as base)
    "UAH/EUR", "UAH/GBP", "UAH/USD", "UAH/CHF", "UAH/PLN",
    # UAH pairs (UAH as target)
    "USD/UAH", "EUR/UAH", "GBP/UAH", "CHF/UAH", "PLN/UAH",
}

# Currency code aliases.
# Keys are matched case-insensitively (see utils.validation.normalize_code),
# so only lowercase forms are needed here. Keep each alias unique.
CURRENCY_ALIASES: Final[dict[str, str]] = {
    # Common typos
    "gpb": "GBP",
    "uds": "USD",
    "eru": "EUR",
    # Full names
    "dollar": "USD",
    "euro": "EUR",
    "pound": "GBP",
    "hryvnia": "UAH",
    "гривна": "UAH",
    "гривня": "UAH",
    "злотий": "PLN",
}

# Number format variations
DECIMAL_SEPARATORS: Final[tuple[str, ...]] = (".", ",")
THOUSAND_SEPARATORS: Final[tuple[str, ...]] = (",", " ", "'", "_", ".")

# Logging Configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
