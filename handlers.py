from datetime import date as date_cls
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message
from utils.memory_store import set_pair, get_pair, delete_pair
from utils.validation import validate_pair_text, normalize_amount
from utils.date_utils import parse_date_any
from services.currency_service import get_major_rate, get_uah_rate
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = Router()

# Characters that carry meaning in Telegram's legacy Markdown parse mode.
# User-provided text (e.g. first_name) must be stripped of these before being
# interpolated into a Markdown message, otherwise it breaks formatting.
_MARKDOWN_CONTROL_CHARS = ("_", "*", "`", "[")

# Characters that may legitimately appear in a numeric amount (digits plus
# thousands/decimal separators). Used to tell an amount apart from a date.
_AMOUNT_CHARS = set("0123456789 .,'_")


def sanitize_markdown(text: str) -> str:
    """Neutralize legacy-Markdown control characters in user-provided text."""
    for ch in _MARKDOWN_CONTROL_CHARS:
        text = text.replace(ch, "")
    return text


def format_date_european(iso_date: str) -> str:
    """Convert YYYY-MM-DD to DD.MM.YYYY"""
    try:
        parts = iso_date.split('-')
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
        return iso_date
    except Exception:
        return iso_date


def _is_amount_like(text: str) -> bool:
    """True if text looks like a numeric amount (digits + number separators)."""
    return bool(text) and any(c.isdigit() for c in text) and all(c in _AMOUNT_CHARS for c in text)


def split_amount_and_date(text: str):
    """Split a message into (amount_str, date_text).

    The date is always the last whitespace-delimited token; everything before
    it is treated as the amount, but only if that leading part actually looks
    like a number. This correctly handles space-separated thousands
    (``1 000,50 yesterday``) and never mistakes a relative-date phrase
    (``2 days ago``) for an amount, since those contain unit words.
    Returns (None, text) when there is no amount.
    """
    tokens = text.split()
    if len(tokens) < 2:
        return None, text
    *amount_part, date_part = tokens
    amount_str = " ".join(amount_part)
    if _is_amount_like(amount_str):
        return amount_str, date_part
    return None, text


@router.message(Command("start", "help"))
async def cmd_help(message: Message):
    """Handle /start and /help commands."""
    user_id = message.from_user.id
    username = sanitize_markdown(message.from_user.first_name or "User")
    logger.info(f"User {user_id} requested help")
    
    text = (
        f"👋 Привіт, {username}!\n\n"
        "💱 **Currency Rate Bot**\n\n"
        "**Команди:**\n"
        "• `/pair BASE/TARGET` — встановити валютну пару\n"
        "  Приклад: `/pair EUR/USD` або `/pair uah usd`\n"
        "• `/reset` — скинути валютну пару\n"
        "• `/help` — показати це повідомлення\n\n"
        "**Використання:**\n"
        "1️⃣ Спочатку встановіть пару: `/pair UAH/USD`\n"
        "2️⃣ Надішліть дату для отримання курсу:\n"
        "   • `21.04.2025`\n"
        "   • `today`, `yesterday`\n"
        "   • `2 days ago`\n"
        "3️⃣ Надішліть суму + дату для конвертації:\n"
        "   • `100 21.04.2025`\n"
        "   • `1000,50 today`\n"
        "   • `1 000,50 yesterday`\n\n"
        "**Підтримувані пари:**\n"
        "Основні: EUR/USD, EUR/GBP, EUR/CHF, USD/EUR, USD/GBP, USD/CHF, EUR/SGD, USD/SGD\n"
        "UAH: UAH/USD, UAH/EUR, UAH/GBP, UAH/CHF, UAH/PLN\n"
        "      USD/UAH, EUR/UAH, GBP/UAH, CHF/UAH, PLN/UAH\n\n"
        "💡 **Підказки:**\n"
        "• Дати у форматі ДД.ММ.РРРР або РРРР-ММ-ДД\n"
        "• Коди валют: UAH, USD, EUR, GBP, CHF, PLN\n"
        "• Суми з комами або пробілами: 1,000.50 або 1 000,50"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("pair"))
async def cmd_pair(message: Message):
    """Handle /pair command to set currency pair."""
    user_id = message.from_user.id
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "❌ Будь ласка, вкажіть валютну пару.\n\n"
                "**Використання:** `/pair UAH/USD`\n\n"
                "Приклади:\n"
                "• `/pair UAH/USD`\n"
                "• `/pair uah usd`\n"
                "• `/pair EUR/UAH`\n"
                "• `/pair PLN/UAH`",
                parse_mode="Markdown"
            )
            return
        
        base, target = validate_pair_text(parts[1])
        await set_pair(user_id, base, target)
        logger.info(f"User {user_id} set pair: {base}/{target}")
        
        await message.answer(
            f"✅ Валютну пару встановлено: **{base}/{target}**\n\n"
            f"Тепер можете надсилати дати для отримання курсів!\n"
            f"Приклад: `21.04.2025` або `100 today`",
            parse_mode="Markdown"
        )
    except ValueError as e:
        logger.warning(f"Validation error for user {user_id}: {e}")
        await message.answer(str(e), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Unexpected error in cmd_pair: {e}", exc_info=True)
        await message.answer("❌ Сталася помилка. Спробуйте ще раз.")


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    """Handle /reset command to clear currency pair."""
    user_id = message.from_user.id
    deleted = await delete_pair(user_id)
    
    if deleted:
        logger.info(f"User {user_id} reset their pair")
        await message.answer(
            "✅ Вашу валютну пару скинуто.\n"
            "Використайте `/pair UAH/USD` щоб встановити нову.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "ℹ️ У вас немає встановленої валютної пари.\n"
            "Використайте `/pair UAH/USD` щоб встановити.",
            parse_mode="Markdown"
        )


@router.message(F.text)
async def on_date_or_amount(message: Message):
    """Handle text messages with dates and optional amounts."""
    user_id = message.from_user.id
    text = message.text.strip()
    
    pair = await get_pair(user_id)
    if not pair:
        logger.info(f"User {user_id} tried to query without setting pair")
        await message.answer(
            "⚠️ Будь ласка, спочатку встановіть валютну пару!\n\n"
            "Використайте: `/pair UAH/USD`\n\n"
            "Див. `/help` для детальної інформації.",
            parse_mode="Markdown"
        )
        return
    
    base, target = pair
    amount = None

    amount_str, date_text = split_amount_and_date(text)
    if amount_str is not None:
        try:
            amount = normalize_amount(amount_str)
            logger.debug(f"Extracted amount: {amount}, date: {date_text}")
        except ValueError as e:
            logger.warning(f"Failed to parse amount: {e}")
            await message.answer(str(e))
            return

    try:
        date = parse_date_any(date_text)
        logger.debug(f"Parsed date: {date} from '{date_text}'")
    except ValueError as e:
        logger.warning(f"Failed to parse date for user {user_id}: {e}")
        await message.answer(str(e), parse_mode="Markdown")
        return
    except Exception as e:
        logger.error(f"Unexpected error parsing date: {e}", exc_info=True)
        await message.answer(
            "❌ Не вдалося розпізнати дату. Використовуйте правильний формат.\n"
            "Приклади: `21.04.2025`, `2025-04-21`, `today`",
            parse_mode="Markdown"
        )
        return

    # Rates for future dates don't exist yet — tell the user directly instead
    # of firing a doomed API request that would just time out with "no data".
    if date > date_cls.today().strftime("%Y-%m-%d"):
        logger.info(f"User {user_id} requested a future date: {date}")
        await message.answer(
            f"📅 Дата {format_date_european(date)} ще не настала — "
            "курс на майбутнє недоступний.\n\n"
            "Спробуйте `today` або минулу дату.",
            parse_mode="Markdown"
        )
        return

    rate_result = None
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Determine which API to use
        if base == "UAH" or target == "UAH":
            rate_result = await get_uah_rate(base, target, date)
        else:
            rate_result = await get_major_rate(base, target, date)

        if rate_result:
            rate, actual_date, is_fallback = rate_result
            logger.info(f"Fetched rate for {base}/{target} on {date}: {rate} (actual: {actual_date}, fallback: {is_fallback})")
    except Exception as e:
        logger.error(f"Error fetching rate: {e}", exc_info=True)
        await message.answer("❌ Не вдалося отримати курс обміну. Спробуйте пізніше.")
        return
    
    if rate_result is None:
        logger.warning(f"No rate found for {base}/{target} on {date}")
        await message.answer(
            f"❌ Немає даних про курс обміну для **{base}/{target}** на {format_date_european(date)}.\n\n"
            "Це може статися якщо:\n"
            "• Дата надто стара\n"
            "• Дата у майбутньому\n"
            "• Це вихідний/свято (спробуйте робочий день)\n"
            "• API тимчасово недоступне\n\n"
            "💡 Спробуйте іншу дату або `/help` для інформації.",
            parse_mode="Markdown"
        )
        return
    
    rate, actual_date, is_fallback = rate_result
    actual_date_eu = format_date_european(actual_date)
    
    fallback_warning = ""
    if is_fallback:
        fallback_warning = f"\n\n⚠️ **Увага:** Курс недоступний на {format_date_european(date)}.\nВикористано найближчу дату: **{actual_date_eu}**"
    
    if amount is not None:
        result = amount * rate
        if result < 0.01:
            result_str = f"{result:.6f}"
        elif result < 1:
            result_str = f"{result:.4f}"
        elif result < 1000:
            result_str = f"{result:.2f}"
        else:
            result_str = f"{result:,.2f}"
        
        response = (
            f"💵 **Результат Конвертації**\n\n"
            f"`{amount:,.2f} {base}` = **{result_str} {target}**\n\n"
            f"📅 Дата: {actual_date_eu}\n"
            f"📊 Курс: 1 {base} = {rate:.6f} {target}"
            f"{fallback_warning}"
        )
        logger.info(f"Conversion: {amount} {base} = {result_str} {target} on {actual_date}")
    else:
        response = (
            f"💱 **Курс Обміну**\n\n"
            f"**{base}/{target}**\n"
            f"1 {base} = **{rate:.6f} {target}**\n\n"
            f"📅 Дата: {actual_date_eu}\n\n"
            f"💡 Підказка: Надішліть `сума дата` для конвертації\n"
            f"Приклад: `100 {actual_date_eu}`"
            f"{fallback_warning}"
        )
        logger.info(f"Rate query: {base}/{target} on {actual_date} = {rate}")
    
    await message.answer(response, parse_mode="Markdown")
