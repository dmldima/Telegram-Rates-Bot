```python
from config import SUPPORTED_PAIRS, CURRENCY_ALIASES

def normalize_code(code: str) -> str:
    code_up = code.upper()
    return CURRENCY_ALIASES.get(code_up, code_up)

def validate_pair_text(text: str) -> tuple[str, str]:
    raw = text.strip().replace(",", " ").replace("/", " ")
    parts = [p for p in raw.split() if p]
    if len(parts) != 2:
        raise ValueError("Invalid pair format. Use /pair EUR/USD")
    base, target = normalize_code(parts[0]), normalize_code(parts[1])
    normalized = f"{base}/{target}"
    if normalized not in SUPPORTED_PAIRS:
        raise ValueError("Unsupported pair. Allowed pairs: " + ", ".join(sorted(SUPPORTED_PAIRS)))
    return base, target
```
