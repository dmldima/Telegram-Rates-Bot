from aiogram import Router, types
from utils.memory_store import set_pair, get_pair
from utils.validation import validate_pair_text
from utils.date_utils import parse_date_any
from services.currency_service import get_major_rate, get_uah_rate

router = Router()

@router.message(commands=["help", "start"])
async def cmd_help(message: types.Message):
    text = (
        "💱 *Currency Rate Bot*\n\n"
        "Commands:\n"
        "/pair BASE/TARGET — set your currency pair (e.g. /pair EUR/USD)\n"
        "/help — show this help message\n\n"
        "Usage:\n"
        "• Send a date (e.g. 01.02.2020) to get the rate for that date.\n"
        "• Send an amount and date (e.g. 100 01.02.2020) to get the converted value.\n\n"
        "Supported pairs:\n"
        "EUR/USD, EUR/GBP, EUR/CHF, USD/EUR, USD/GBP, USD/CHF, EUR/SGD, USD/SGD,\n"
        "UAH/EUR, UAH/GBP, UAH/USD"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(commands=["pair"])
async def cmd_pair(message: types.Message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Usage: /pair EUR/USD")
            return
        base, target = validate_pair_text(parts[1])
        set_pair(message.from_user.id, base, target)
        await message.answer(f"✅ Pair set to {base}/{target}")
    except Exception as e:
        await message.answer(str(e))

@router.message()
async def on_date_or_amount(message: types.Message):
    pair = get_pair(message.from_user.id)
    if not pair:
        await message.answer("Please set a pair first: /pair EUR/USD")
        return

    base, target = pair
    text = message.text.strip()
    amount = None
    date_text = text

    parts = text.split()
    if len(parts) >= 2 and parts[0].replace('.', '', 1).isdigit():
        try:
            amount = float(parts[0])
            date_text = ' '.join(parts[1:])
        except ValueError:
            amount = None

    try:
        date = parse_date_any(date_text)
    except Exception:
        await message.answer("Invalid date.")
        return

    rate = None
    try:
        if base == "UAH":
            rate = await get_uah_rate(base, target, date)
        else:
            rate = await get_major_rate(base, target, date)
    except Exception:
        rate = None

    if rate is None:
        await message.answer("No data.")
        return

    if amount is not None:
        result = round(amount * rate, 4)
        await message.answer(str(result))
    else:
        await message.answer(str(rate))
