import aiohttp
import asyncio
from typing import Optional, Tuple
from datetime import datetime, timedelta
from config import (
    FRANKFURTER_BASE_URL, NBU_BASE_URL, EXCHANGERATE_API_URL,
    REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY,
    USE_FALLBACK_DATE, MAX_FALLBACK_DAYS
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

_rate_cache: dict[str, tuple[float, datetime, str]] = {}
CACHE_TTL = timedelta(hours=1)

def _get_cache_key(base: str, target: str, date: str) -> str:
    return f"{base}/{target}:{date}"

def _get_cached_rate(base: str, target: str, date: str) -> Optional[Tuple[float, str]]:
    key = _get_cache_key(base, target, date)
    if key in _rate_cache:
        rate, timestamp, actual_date = _rate_cache[key]
        if datetime.now() - timestamp < CACHE_TTL:
            logger.debug(f"Cache hit for {key}")
            return (rate, actual_date)
        else:
            del _rate_cache[key]
    return None

def _cache_rate(base: str, target: str, requested_date: str, rate: float, actual_date: str) -> None:
    key = _get_cache_key(base, target, requested_date)
    _rate_cache[key] = (rate, datetime.now(), actual_date)
    logger.debug(f"Cached rate for {key}: {rate} (actual date: {actual_date})")

async def _http_json_with_retry(url: str, max_retries: int = MAX_RETRIES) -> Optional[dict]:
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
                        logger.warning(f"Server error {resp.status}, retrying...")
                        last_error = f"Server error: {resp.status}"
                    else:
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
        
        if attempt < max_retries - 1:
            delay = RETRY_DELAY * (2 ** attempt)
            await asyncio.sleep(delay)
    
    logger.error(f"All retry attempts failed for {url}: {last_error}")
    return None

async def _get_closest_rate_frankfurter(base: str, target: str, requested_date: str) -> Optional[Tuple[float, str]]:
    url = f"{FRANKFURTER_BASE_URL}/{requested_date}?from={base}&to={target}"
    data = await _http_json_with_retry(url)
    
    if data and "rates" in data and target in data["rates"]:
        rate = float(data["rates"][target])
        actual_date = data.get("date", requested_date)
        return (rate, actual_date)
    
    if USE_FALLBACK_DATE:
        logger.info(f"No rate for {requested_date}, looking for closest previous date...")
        req_date = datetime.strptime(requested_date, "%Y-%m-%d").date()
        
        for days_back in range(1, MAX_FALLBACK_DAYS + 1):
            fallback_date = req_date - timedelta(days=days_back)
            fallback_str = fallback_date.strftime("%Y-%m-%d")
            url = f"{FRANKFURTER_BASE_URL}/{fallback_str}?from={base}&to={target}"
            data = await _http_json_with_retry(url)
            
            if data and "rates" in data and target in data["rates"]:
                rate = float(data["rates"][target])
                actual_date = data.get("date", fallback_str)
                logger.info(f"Found rate from {actual_date} (fallback from {requested_date})")
                return (rate, actual_date)
    return None

async def _try_exchangerate_api_backup(base: str, target: str, requested_date: str) -> Optional[Tuple[float, str]]:
    try:
        if requested_date == datetime.now().strftime("%Y-%m-%d"):
            url = f"{EXCHANGERATE_API_URL}/{base}"
            data = await _http_json_with_retry(url)
            if data and "rates" in data and target in data["rates"]:
                rate = float(data["rates"][target])
                actual_date = data.get("date", requested_date)
                logger.info(f"Got rate from backup API (exchangerate-api)")
                return (rate, actual_date)
    except Exception as e:
        logger.warning(f"Backup API failed: {e}")
    return None

async def get_major_rate(base: str, target: str, date: str) -> Optional[Tuple[float, str, bool]]:
    cached = _get_cached_rate(base, target, date)
    if cached is not None:
        rate, actual_date = cached
        is_fallback = (actual_date != date)
        return (rate, actual_date, is_fallback)
    
    try:
        result = await _get_closest_rate_frankfurter(base, target, date)
        if result:
            rate, actual_date = result
            is_fallback = (actual_date != date)
            _cache_rate(base, target, date, rate, actual_date)
            logger.info(f"Rate {base}/{target} on {date}: {rate} (actual: {actual_date})")
            return (rate, actual_date, is_fallback)
        
        result = await _try_exchangerate_api_backup(base, target, date)
        if result:
            rate, actual_date = result
            is_fallback = (actual_date != date)
            _cache_rate(base, target, date, rate, actual_date)
            return (rate, actual_date, is_fallback)
        
        logger.warning(f"No rate found for {base}/{target} on {date}")
        return None
    except Exception as e:
        logger.error(f"Error getting major rate: {e}")
        return None

async def _get_closest_rate_nbu(base: str, target: str, requested_date: str) -> Optional[Tuple[float, str]]:
    yyyymmdd = requested_date.replace("-", "")
    url = f"{NBU_BASE_URL}?valcode={target}&date={yyyymmdd}&json"
    data = await _http_json_with_retry(url)
    
    if data and isinstance(data, list) and len(data) > 0:
        rec = data[0]
        uah_per_target = float(rec.get("rate", 0))
        if uah_per_target > 0:
            rate = 1.0 / uah_per_target
            actual_date = rec.get("exchangedate", requested_date)
            if '.' in actual_date:
                parts = actual_date.split('.')
                if len(parts) == 3:
                    actual_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
            return (rate, actual_date)
    
    if USE_FALLBACK_DATE:
        logger.info(f"No NBU rate for {requested_date}, looking for closest previous date...")
        req_date = datetime.strptime(requested_date, "%Y-%m-%d").date()
        
        for days_back in range(1, MAX_FALLBACK_DAYS + 1):
            fallback_date = req_date - timedelta(days=days_back)
            fallback_yyyymmdd = fallback_date.strftime("%Y%m%d")
            url = f"{NBU_BASE_URL}?valcode={target}&date={fallback_yyyymmdd}&json"
            data = await _http_json_with_retry(url)
            
            if data and isinstance(data, list) and len(data) > 0:
                rec = data[0]
                uah_per_target = float(rec.get("rate", 0))
                if uah_per_target > 0:
                    rate = 1.0 / uah_per_target
                    actual_date = fallback_date.strftime("%Y-%m-%d")
                    logger.info(f"Found NBU rate from {actual_date} (fallback from {requested_date})")
                    return (rate, actual_date)
    return None

async def get_uah_rate(base: str, target: str, date: str) -> Optional[Tuple[float, str, bool]]:
    if base != "UAH":
        logger.error(f"get_uah_rate called with base={base}, expected UAH")
        return None
    
    cached = _get_cached_rate(base, target, date)
    if cached is not None:
        rate, actual_date = cached
        is_fallback = (actual_date != date)
        return (rate, actual_date, is_fallback)
    
    try:
        result = await _get_closest_rate_nbu(base, target, date)
        if result:
            rate, actual_date = result
            is_fallback = (actual_date != date)
            _cache_rate(base, target, date, rate, actual_date)
            logger.info(f"Rate {base}/{target} on {date}: {rate} (actual: {actual_date})")
            return (rate, actual_date, is_fallback)
        
        logger.warning(f"No NBU rate found for {base}/{target} on {date}")
        return None
    except Exception as e:
        logger.error(f"Error getting UAH rate: {e}")
        return None

def clear_cache() -> int:
    count = len(_rate_cache)
    _rate_cache.clear()
    logger.info(f"Cleared {count} cached rates")
    return count

def get_cache_stats() -> dict:
    return {"entries": len(_rate_cache), "ttl_hours": CACHE_TTL.total_seconds() / 3600}
