```md
# Currency Rate Bot (Telegram) — Koyeb Ready

A Telegram bot that:
- Lets each user set a currency **pair** (from a fixed allowlist)
- Accepts a **date in many formats**
- Replies with either the **numeric rate** or **converted amount** if an amount is provided
- Supports UAH pairs via **NBU** API; other majors via **Frankfurter**

## Supported pairs
- Major: `EUR/USD`, `EUR/GBP`, `EUR/CHF`, `USD/EUR`, `USD/GBP`, `USD/CHF`, `EUR/SGD`, `USD/SGD`
- UAH: `UAH/EUR`, `UAH/GBP`, `UAH/USD`

## Commands
- `/pair EUR/USD` — set pair for the current user
- `/help` — show help and usage instructions
- Send a **date** like `01.02.2020` or include an **amount** such as `100 01.02.2020`. The bot replies with:
  - just the rate (if no amount provided)
  - the converted value (if amount provided)

Example:
```
/pair usd/eur
100 02.01.2020
```
→ `89.6` (conversion result)

If no pair is set, the bot prompts: `Please set a pair first: /pair EUR/USD`.

Environment variables should be configured through **GitHub Secrets**:
- `BOT_TOKEN`
- `WEBHOOK_URL`

Deploy to Koyeb using GitHub integration.
```
