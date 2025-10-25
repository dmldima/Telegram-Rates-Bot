import aiohttp

FRANKFURTER_BASE = "https://api.frankfurter.app"
NBU_BASE = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"

async def _http_json(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

async def get_major_rate(base: str, target: str, date: str) -> float | None:
    url = f"{FRANKFURTER_BASE}/{date}?from={base}&to={target}"
    data = await _http_json(url)
    if not data:
        return None
    return data.get("rates", {}).get(target)

async def get_uah_rate(base: str, target: str, date: str) -> float | None:
    yyyymmdd = date.replace("-", "")
    url = f"{NBU_BASE}?valcode={target}&date={yyyymmdd}&json"
    data = await _http_json(url)
    if not data:
        return None
    try:
        rec = data[0]
        uah_per_target = float(rec["rate"])
        if uah_per_target <= 0:
            return None
        return 1.0 / uah_per_target
    except Exception:
        return None
