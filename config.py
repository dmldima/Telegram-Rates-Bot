"""
Configuration module for Currency Rate Bot.
Contains supported pairs, aliases, and API settings.
"""
import os
from typing import Final

# API Configuration - Primary and Backup sources
FRANKFURTER_BASE_URL: Final[str] = "https://api.frankfurter.app"
FRANKFURTER_BACKUP_URL: Final[str] = "https://www.frankfurter.app"

NBU_BASE_URL: Final[str] = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
NBU_BACKUP_URL: Final[str] = "https://bank.gov.ua/NBU_Exchange/exchange_site"

# Additional backup APIs for major currencies
EXCHANGERATE_API_URL: Final[str] = "https://api.exchangerate-api.com/v4/latest"
FIXER_API_URL: Final[str] = "https://api.fixer.io/latest"  # Requires API key
ECB_API_URL: Final[str] = "https://sdw-wsrest.ecb.europa.eu/service/data/EXR"

# Fallback behavior
USE_FALLBACK_DATE: Final[bool] = True  # Use closest available date if exact date not found
MAX_FALLBACK_DAYS: Final[int] = 7  # Maximum days to look back for rate

# HTTP Settings
REQUEST_TIMEOUT: Final[int] = 10  # seconds
MAX_RETRIES: Final[int] = 3
RETRY_DELAY: Final[float] = 1.0  # seconds

# Bot Settings
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
PORT: int = int(os.getenv("PORT", "8080"))

# Redis Configuration (optional, for persistent storage)
REDIS_URL: str = os.getenv("REDIS_URL", "")
USE_REDIS: bool = bool(REDIS_URL)

# Supported currency pairs
SUPPORTED_PAIRS: Final[set[str]] = {
    # Major pairs
    "EUR/USD", "EUR/GBP", "EUR/CHF", 
    "USD/EUR", "USD/GBP", "USD/CHF", 
    "EUR/SGD", "USD/SGD",
    # UAH pairs
    "UAH/EUR", "UAH/GBP", "UAH/USD",
}

# Currency code aliases for common typos and variations
CURRENCY_ALIASES: Final[dict[str, str]] = {
    # Common typos
    "GPB": "GBP",
    "gpb": "GBP",
    "UDS": "USD",
    "uds": "USD",
    "ERU": "EUR",
    "eur": "EUR",
    # Alternative names
    "DOLLAR": "USD",
    "EURO": "EUR",
    "POUND": "GBP",
    "HRYVNIA": "UAH",
    "ГРИВНА": "UAH",
    # Lowercase versions
    "eur": "EUR",
    "usd": "USD",
    "gbp": "GBP",
    "chf": "CHF",
    "sgd": "SGD",
    "uah": "UAH",
}

# Number format variations
DECIMAL_SEPARATORS: Final[tuple[str, ...]] = (".", ",")
THOUSAND_SEPARATORS: Final[tuple[str, ...]] = (",", " ", "'", "_", ".")

# Logging Configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
