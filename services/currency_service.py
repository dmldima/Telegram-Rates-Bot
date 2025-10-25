"""
Currency rate service with improved error handling and caching.
Supports Frankfurter API for major currencies and NBU API for UAH.
"""
import aiohttp
import asyncio
from typing import Optional
from functools import lru_cache
from datetime import datetime, timedelta
from config import (
    FRANKFURTER_BASE_URL,
    NBU_BASE_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Simple in-memory cache
_rate_cache: dict[str, tuple[float, datetime]] = {}
CACHE_TTL = timedelta(hours=1)


def _get_cache_key(base: str, target: str, date: str) -> str:
    """Generate cache key for rate."""
    return f"{base}/{target}:{date}"


def _get_cached_rate(base: str, target: str, date: str) -> Optional[float]:
    """Retrieve rate from cache if not expired."""
    key = _get_cache_key(base, target, date)
    
    if key in _rate_cache:
        rate, timestamp = _rate_cache[key]
        if datetime.now() - timestamp < CACHE_TTL:
            logger.debug(f"Cache hit for {key}")
            return rate
        else:
            # Remove expired entry
            del _rate_cache[key]
    
    return None


def _cache_rate(base: str, target: str, date: str, rate: float) -> None:
    """Store rate in cache."""
    key = _get_cache_key(base, target, date)
    _rate_cache[key] = (rate, datetime.now())
    logger.debug(f"Cached rate for {key}: {rate}")


async def _http_json_with_retry(
    url: str,
    max_retries: int = MAX_RETRIES
) -> Optional[dict]:
    """
    Fetch JSON from URL with retry logic.
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        
    Returns:
        Parsed JSON data or None on failure
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.debug(f"Successfully fetched {url}")
                        return data
                    elif resp.status == 404:
                        logger.warning(f"Data not found: {url}")
                        return None
                    elif resp.status >= 500:
                        # Server error, retry
                        logger.warning(f"Server error {resp.status}, retrying...")
                        last_error = f"Server error: {resp.status}"
                    else:
                        # Client error, don't retry
                        logger.error(f"Client error {resp.status}: {url}")
                        return None
        
        except asyncio.TimeoutError:
            last_error = "Request timeout"
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
        
        except aiohttp.ClientError as e:
            last_error = str(e)
            logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
        
        except Exception as e:
            last_error = str(e)
            logger.error(f"Unexpected error: {e}")
            return None
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            delay = RETRY_DELAY * (2 ** attempt)
            await asyncio.sleep(delay)
    
    logger.error(f"All retry attempts failed for {url}: {last_error}")
    return None


async def get_major_rate(
    base: str,
    target: str,
    date: str
) -> Optional[float]:
    """
    Get exchange rate for major currency pairs via Frankfurter API.
    
    Args:
        base: Base currency code (e.g., 'EUR')
        target: Target currency code (e.g., 'USD')
        date: Date in ISO format (YYYY-MM-DD)
        
    Returns:
        Exchange rate or None if not available
    """
    # Check cache first
    cached = _get_cached_rate(base, target, date)
    if cached is not None:
        return cached
    
    url = f"{FRANKFURTER_BASE_URL}/{date}?from={base}&to={target}"
    
    try:
        data = await _http_json_with_retry(url)
        if not data:
            logger.warning(f"No data for {base}/{target} on {date}")
            return None
        
        rate = data.get("rates", {}).get(target)
        
        if rate is not None:
            # Cache the result
            _cache_rate(base, target, date, rate)
            logger.info(f"Rate {base}/{target} on {date}: {rate}")
            return float(rate)
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting major rate: {e}")
        return None


async def get_uah_rate(
    base: str,
    target: str,
    date: str
) -> Optional[float]:
    """
    Get exchange rate for UAH pairs via NBU API.
    
    Args:
        base: Base currency code (must be 'UAH')
        target: Target currency code (e.g., 'USD')
        date: Date in ISO format (YYYY-MM-DD)
        
    Returns:
        Exchange rate (UAH per 1 target currency) or None
    """
    if base != "UAH":
        logger.error(f"get_uah_rate called with base={base}, expected UAH")
        return None
    
    # Check cache first
    cached = _get_cached_rate(base, target, date)
    if cached is not None:
        return cached
    
    # Convert date format: YYYY-MM-DD -> YYYYMMDD
    yyyymmdd = date.replace("-", "")
    
    url = f"{NBU_BASE_URL}?valcode={target}&date={yyyymmdd}&json"
    
    try:
        data = await _http_json_with_retry(url)
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No NBU data for {target} on {date}")
            return None
        
        rec = data[0]
        uah_per_target = float(rec.get("rate", 0))
        
        if uah_per_target <= 0:
            logger.error(f"Invalid rate from NBU: {uah_per_target}")
            return None
        
        # Rate is UAH per 1 target currency, so we need to invert it
        # to get target currency per 1 UAH
        rate = 1.0 / uah_per_target
        
        # Cache the result
        _cache_rate(base, target, date, rate)
        logger.info(f"Rate {base}/{target} on {date}: {rate}")
        
        return rate
    
    except Exception as e:
        logger.error(f"Error getting UAH rate: {e}")
        return None


def clear_cache() -> int:
    """
    Clear rate cache.
    
    Returns:
        Number of entries cleared
    """
    count = len(_rate_cache)
    _rate_cache.clear()
    logger.info(f"Cleared {count} cached rates")
    return count


def get_cache_stats() -> dict:
    """
    Get cache statistics.
    
    Returns:
        Dict with cache info
    """
    return {
        "entries": len(_rate_cache),
        "ttl_hours": CACHE_TTL.total_seconds() / 3600
    }
