```python
from datetime import datetime
from dateutil import parser as dtparser

def _split_nums(date_str: str) -> list[int]:
    parts = [p for p in date_str.replace(".", "/").replace("-", "/").split("/") if p]
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            pass
    return nums

def parse_date_any(date_text: str) -> str:
    s = date_text.strip()
    nums = _split_nums(s)
    yearfirst = False
    dayfirst = True
    if len(s) >= 4 and s[:4].isdigit():
        yearfirst = True
        dayfirst = False
    elif len(nums) >= 2:
        a, b = nums[0], nums[1]
        if a > 12 and b <= 12:
            dayfirst = True
        elif a <= 12 and b > 12:
            dayfirst = False
        else:
            dayfirst = True
    dt = dtparser.parse(s, dayfirst=dayfirst, yearfirst=yearfirst, fuzzy=True)
    return dt.strftime("%Y-%m-%d")
```
