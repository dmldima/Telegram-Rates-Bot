import re
from typing import Tuple
from config import SUPPORTED_PAIRS, CURRENCY_ALIASES
from utils.logger import setup_logger

logger = setup_logger(__name__)

def normalize_code(code: str) -> str:
    code = code.strip()
    code_lower = code.lower()
    for alias, canonical in CURRENCY_ALIASES.items():
        if alias.lower() == code_lower:
            logger.debug(f"Normalized alias '{code}' to '{canonical}'")
            return canonical
    normalized = code.upper()
    normalized = re.sub(r'[^A-Z]', '', normalized)
    return normalized

def validate_pair_text(text: str) -> Tuple[str, str]:
    if not text or not text.strip():
        raise ValueError("❌ Pair cannot be empty. Use format: /pair EUR/USD")
    normalized = text.strip()
    normalized = re.sub(r'[/\-,\s]+', ' ', normalized)
    parts = [p.strip() for p in normalized.split() if p.strip()]
    
    if len(parts) < 2:
        raise ValueError(
            "❌ Invalid pair format. Use: /pair EUR/USD\n"
            "Supported formats: EUR/USD, EUR USD, EUR-USD, eur,usd"
        )
    if len(parts) > 2:
        logger.warning(f"Extra parts in pair input: {parts}")
        parts = parts[:2]
    
    try:
        base = normalize_code(parts[0])
        target = normalize_code(parts[1])
    except Exception as e:
        logger.error(f"Error normalizing codes: {e}")
        raise ValueError(f"❌ Invalid currency codes: {parts[0]}, {parts[1]}")
    
    if not base or not target:
        raise ValueError("❌ Currency codes cannot be empty")
    if base == target:
        raise ValueError(f"❌ Base and target currency cannot be the same: {base}")
    
    pair = f"{base}/{target}"
    if pair not in SUPPORTED_PAIRS:
        raise ValueError(
            f"❌ Pair {pair} is not supported.\n\n"
            f"Supported pairs:\n{_format_supported_pairs()}"
        )
    logger.info(f"Validated pair: {pair}")
    return base, target

def _format_supported_pairs() -> str:
    major = [p for p in sorted(SUPPORTED_PAIRS) if not p.startswith("UAH")]
    uah = [p for p in sorted(SUPPORTED_PAIRS) if p.startswith("UAH")]
    result = "Major pairs:\n" + ", ".join(major)
    if uah:
        result += "\n\nUAH pairs:\n" + ", ".join(uah)
    return result

def normalize_amount(amount_str: str) -> float:
    if not amount_str or not amount_str.strip():
        raise ValueError("Amount cannot be empty")
    
    cleaned = amount_str.strip()
    dot_count = cleaned.count('.')
    comma_count = cleaned.count(',')
    space_count = cleaned.count(' ')
    apostrophe_count = cleaned.count("'")
    last_dot_pos = cleaned.rfind('.')
    last_comma_pos = cleaned.rfind(',')
    
    if dot_count == 0 and comma_count == 0:
        cleaned = cleaned.replace(' ', '').replace("'", '').replace('_', '')
    elif dot_count == 0 and comma_count == 1:
        parts = cleaned.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(' ', '').replace("'", '').replace('_', '')
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '').replace(' ', '').replace("'", '').replace('_', '')
    elif comma_count == 0 and dot_count == 1:
        parts = cleaned.split('.')
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(' ', '').replace("'", '').replace('_', '').replace(',', '')
        else:
            cleaned = cleaned.replace('.', '').replace(' ', '').replace("'", '').replace('_', '')
    elif dot_count > 1 and comma_count == 0:
        cleaned = cleaned.replace('.', '').replace(' ', '').replace("'", '').replace('_', '')
    elif comma_count > 1 and dot_count == 0:
        cleaned = cleaned.replace(',', '').replace(' ', '').replace("'", '').replace('_', '')
    elif dot_count >= 1 and comma_count >= 1:
        if last_comma_pos > last_dot_pos:
            cleaned = cleaned.replace(' ', '').replace("'", '').replace('_', '')
            cleaned = cleaned.replace('.', '')
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(' ', '').replace("'", '').replace('_', '')
            cleaned = cleaned.replace(',', '')
    elif space_count > 0 or apostrophe_count > 0:
        if last_comma_pos > last_dot_pos:
            cleaned = cleaned.replace(' ', '').replace("'", '').replace('_', '')
            cleaned = cleaned.replace('.', '')
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(' ', '').replace("'", '').replace('_', '')
            cleaned = cleaned.replace(',', '')
    
    try:
        value = float(cleaned)
        if value < 0:
            raise ValueError("Amount cannot be negative")
        if value == 0:
            raise ValueError("Amount cannot be zero")
        return value
    except ValueError as e:
        logger.error(f"Failed to parse amount '{amount_str}': {e}")
        raise ValueError(
            f"❌ Invalid amount format: {amount_str}\n"
            "Supported formats:\n"
            "• 100 or 100.50 or 100,50\n"
            "• 1,000.50 (US format)\n"
            "• 1.000,50 (European format)\n"
            "• 1 000,50 or 1 000.50\n"
            "• 1'000.50 (Swiss format)\n"
            "• 1.234.567,89 or 1,234,567.89"
        )
