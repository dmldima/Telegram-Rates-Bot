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

@router.message(Command("start", "help"))
async def cmd_help(message: Message):
    """Handle /start and /help commands."""
    user_id = message.from_user.id
    username = message.from_user.first_name or "User"
    logger.info(f"User {user_id} ({username}) requested help")
    
    text = (
        f"👋 Hi {username}!\n\n"
        "💱 **Currency Rate Bot**\n\n"
        "**Commands:**\n"
        "• `/pair BASE/TARGET` — set your currency pair\n"
        "  Example: `/pair EUR/USD` or `/pair eur usd`\n"
        "• `/reset` — reset your currency pair\n"
        "• `/help` — show this message\n\n"
        "**Usage:**\n"
        "1️⃣ Set your pair first: `/pair EUR/USD`\n"
        "2️⃣ Send a date to get the rate:\n"
        "   • `01.02.2020`\n"
        "   • `2020-02-01`\n"
        "   • `today`, `yesterday`\n"
        "   • `2 days ago`\n"
        "3️⃣ Send amount + date for conversion:\n"
        "   • `100 01.02.2020`\n"
        "   • `1,000.50 today`\n"
        "   • `1 000,50 yesterday`\n\n"
        "**Supported pairs:**\n"
        "Major: EUR/USD, EUR/GBP, EUR/CHF, USD/EUR, USD/GBP, USD/CHF, EUR/SGD, USD/SGD\n"
        "UAH: UAH/EUR, UAH/GBP, UAH/USD\n\n"
        "💡 **Tips:**\n"
        "• You can use different date formats (DD.MM.YYYY, YYYY-MM-DD, etc.)\n"
        "• Amounts can have commas or spaces (1,000.50 or 1 000,50)\n"
        "• Currency codes are case-insensitive (eur/usd or EUR/USD)"
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
                "❌ Please specify a currency pair.\n
                "\n**Usage:** `/pair EUR/USD`\n\n"
                "Examples:\n"
                "• `/pair EUR/USD`\n"
                "• `/pair eur usd`\n"
                "• `/pair EUR-GBP`\n"
                "• `/pair uah/usd`",
                parse_mode="Markdown"
            )
            return
        
        base, target = validate_pair_text(parts[1])
        set_pair(user_id, base, target)
        logger.info(f"User {user_id} set pair: {base}/{target}")
        
        await message.answer(
            f"✅ Currency pair set to **{base}/{target}**\n\n"
            f"Now you can send dates to get rates!\n"
            f"Example: `01.02.2020` or `100 today`",
            parse_mode="Markdown"
        )
    except ValueError as e:
        logger.warning(f"Validation error for user {user_id}: {e}")
        await message.answer(str(e), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Unexpected error in cmd_pair: {e}", exc_info=True)
        await message.answer("❌ An error occurred. Please try again or contact support.")

@router.message(Command("reset"))
async def cmd_reset(message: Message):
    """Handle /reset command to clear currency pair."""
    user_id = message.from_user.id
    deleted = delete_pair(user_id)
    
    if deleted:
        logger.info(f"User {user_id} reset their pair")
        await message.answer(
            "✅ Your currency pair has been reset.\n"
            "Use `/pair EUR/USD` to set a new one.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "ℹ️ You don't have a currency pair set.\n"
            "Use `/pair EUR/USD` to set one.",
            parse_mode="Markdown"
        )

@router.message(F.text)
async def on_date_or_amount(message: Message):
    """Handle text messages with dates and optional amounts."""
    user_id = message.from_user.id
    text = message.text.strip()
    
    pair = get_pair(user_id)
    if not pair:
        logger.info(f"User {user_id} tried to query without setting pair")
        await message.answer(
            "⚠️ Please set a currency pair first!\n\n"
            "Use: `/pair EUR/USD`\n\n"
            "See `/help` for more information.",
            parse_mode="Markdown"
        )
        return
    
    base, target = pair
    amount = None
    date_text = text
    
    parts = text.split(maxsplit=1)
    if len(parts) >= 2:
        first_part = parts[0].replace(',', '').replace(' ', '').replace('.', '', 1)
        if first_part.replace('.', '', 1).isdigit() or first_part.replace(',', '', 1).isdigit():
            try:
                amount = normalize_amount(parts[0])
                date_text = parts[1]
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
            "❌ Could not parse date. Please use a valid format.\n"
            "Examples: `01.02.2020`, `2020-02-01`, `today`",
            parse_mode="Markdown"
        )
        return
    
    rate_result = None
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        if base == "UAH":
            rate_result = await get_uah_rate(base, target, date)
        else:
            rate_result = await get_major_rate(base, target, date)
        
        if rate_result:
            rate, actual_date, is_fallback = rate_result
            logger.info(f"Fetched rate for {base}/{target} on {date}: {rate} (actual: {actual_date}, fallback: {is_fallback})")
        else:
            rate_result = None
    except Exception as e:
        logger.error(f"Error fetching rate: {e}", exc_info=True)
        await message.answer("❌ Failed to fetch exchange rate. Please try again later.")
        return
    
    if rate_result is None:
        logger.warning(f"No rate found for {base}/{target} on {date}")
        await message.answer(
            f"❌ No exchange rate data available for **{base}/{target}** on {date}.\n\n"
            "This could happen if:\n"
            "• The date is too old (check API limits)\n"
            "• The date is in the future\n"
            "• It's a weekend/holiday (try a business day)\n"
            "• The API is temporarily unavailable\n\n"
            "💡 Try a different date or use `/help` for more info.",
            parse_mode="Markdown"
        )
        return
    
    rate, actual_date, is_fallback = rate_result
    fallback_warning = ""
    if is_fallback:
        fallback_warning = f"\n\n⚠️ **Note:** Rate not available for {date}.\nUsing closest available date: **{actual_date}**"
    
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
            f"💵 **Conversion Result**\n\n"
            f"`{amount:,.2f} {base}` = **{result_str} {target}**\n\n"
            f"📅 Date: {actual_date}\n"
            f"📊 Rate: 1 {base} = {rate:.6f} {target}"
            f"{fallback_warning}"
        )
        logger.info(f"Conversion: {amount} {base} = {result_str} {target} on {actual_date}")
    else:
        response = (
            f"💱 **Exchange Rate**\n\n"
            f"**{base}/{target}**\n"
            f"1 {base} = **{rate:.6f} {target}**\n\n"
            f"📅 Date: {actual_date}\n\n"
            f"💡 Tip: Send `amount date` to convert\n"
            f"Example: `100 {actual_date}`"
            f"{fallback_warning}"
        )
        logger.info(f"Rate query: {base}/{target} on {actual_date} = {rate}")
    
    await message.answer(response, parse_mode="Markdown")
