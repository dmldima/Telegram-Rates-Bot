# 💱 Currency Rate Bot for Telegram

Modern, production-ready Telegram bot for currency exchange rates with support for multiple date formats, amount normalization, and intelligent error handling.

## ✨ Features

- **Smart Currency Pair Management**: Each user can set their preferred currency pair
- **Flexible Date Parsing**: Supports multiple date formats (DD.MM.YYYY, YYYY-MM-DD, natural language)
- **Intelligent Fallback Dates**: If exact date unavailable, automatically finds closest previous date (within 7 days)
- **Amount Normalization**: Handles various number formats (1,000.50, 1.000,50, 1 000,50, 1'000.50, 1.234.567,89)
- **Intelligent Input Recognition**: Automatically corrects common typos in currency codes
- **Multiple API Sources**:
  - **Primary**: Frankfurter API for major currency pairs
  - **Primary**: NBU API for Ukrainian Hryvnia (UAH) pairs
  - **Backup**: ExchangeRate-API for current rates
- **Production Ready**:
  - Retry logic with exponential backoff
  - Response caching (1-hour TTL)
  - Multiple API fallbacks
  - Comprehensive logging
  - Error handling
  - Optional Redis storage

## 🚀 Supported Pairs

### Major Currencies
`EUR/USD`, `EUR/GBP`, `EUR/CHF`, `USD/EUR`, `USD/GBP`, `USD/CHF`, `EUR/SGD`, `USD/SGD`

### Ukrainian Hryvnia
`UAH/EUR`, `UAH/GBP`, `UAH/USD`

## 📋 Commands

- `/start` or `/help` — Show help message
- `/pair BASE/TARGET` — Set your currency pair (e.g., `/pair EUR/USD`)
- `/reset` — Clear your currency pair

## 💡 Usage Examples

### 1. Set Currency Pair
```
/pair EUR/USD
/pair eur usd
/pair EUR-GBP
/pair uah/usd
```

### 2. Get Exchange Rate
Send a date in any format:
```
01.02.2020
2020-02-01
01-02-2020
today
yesterday
2 days ago
```

### 3. Convert Amount
Send amount + date:
```
100 01.02.2020
1,000.50 today
1 000,50 yesterday
50 2 days ago
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Local Development (Polling Mode)

1. Clone the repository
```bash
git clone <your-repo>
cd currency-bot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set environment variable
```bash
export BOT_TOKEN="your_bot_token_here"
```

4. Run in development mode
```bash
python dev_polling.py
```

### Production Deployment (Webhook Mode)

#### Deploy to Koyeb

1. Fork/clone this repository to GitHub

2. Create a new app on [Koyeb](https://www.koyeb.com/)

3. Connect your GitHub repository

4. Set environment variables in Koyeb:
   - `BOT_TOKEN`: Your Telegram bot token
   - `WEBHOOK_URL`: `https://your-app.koyeb.app` (Koyeb will provide this)
   - `PORT`: `8080` (default)
   - `LOG_LEVEL`: `INFO` (optional, default: INFO)
   - `REDIS_URL`: Redis connection URL (optional, for persistent storage)

5. Deploy!

The bot will automatically:
- Set up webhook
- Handle incoming updates
- Provide health check endpoint at `/health`

## 🏗️ Project Structure

```
currency-bot/
├── config.py                      # Configuration and constants
├── main.py                        # Production entry point (webhook)
├── dev_polling.py                 # Development entry point (polling)
├── handlers.py                    # Bot command and message handlers
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── services/
│   └── currency_service.py        # API clients with retry logic
└── utils/
    ├── logger.py                  # Logging configuration
    ├── validation.py              # Input validation and normalization
    ├── date_utils.py              # Date parsing utilities
    └── memory_store.py            # User preferences storage
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | - | Telegram Bot API token |
| `WEBHOOK_URL` | Yes (prod) | - | Full webhook URL for production |
| `PORT` | No | 8080 | Port for webhook server |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `REDIS_URL` | No | - | Redis connection URL for persistent storage |

### Storage Options

**In-Memory (Default)**:
- Simple, no setup required
- Data is lost on restart
- Good for development and small bots

**Redis (Optional)**:
- Persistent storage
- Survives restarts
- Recommended for production
- Set `REDIS_URL` environment variable

## 📊 API Sources

### Frankfurter API
- **URL**: https://api.frankfurter.app
- **Currencies**: Major world currencies (EUR, USD, GBP, CHF, SGD, etc.)
- **Update Frequency**: Daily (business days)
- **Free**: Yes, no API key required

### NBU (National Bank of Ukraine)
- **URL**: https://bank.gov.ua/NBUStatService
- **Currencies**: UAH exchange rates
- **Update Frequency**: Daily
- **Free**: Yes, no API key required

## 🎨 Features Highlights

### Smart Input Recognition
The bot automatically handles:
- **Typos**: `gpb` → `GBP`, `uds` → `USD`
- **Case**: `eur`, `EUR`, `Eur` all work
- **Separators**: `/`, `-`, `,`, space all work
- **Alternative names**: `dollar` → `USD`, `euro` → `EUR`

### Flexible Date Formats
Supported formats:
- `DD.MM.YYYY` (European): `01.02.2020`
- `MM/DD/YYYY` (American): `02/01/2020`
- `YYYY-MM-DD` (ISO): `2020-02-01`
- Natural language: `today`, `yesterday`, `2 days ago`
- Ukrainian: `сьогодні`, `вчора`

### Amount Normalization
Handles various number formats:
- `1000.50` (standard)
- `1,000.50` (US format)
- `1 000,50` (European format)
- `1'000.50` (Swiss format)

## 🐛 Troubleshooting

### Bot doesn't respond
1. Check `BOT_TOKEN` is correctly set
2. Check bot is not blocked by user
3. Check logs for errors

### "No data available"
- Date might be too old or in the future
- Weekend/holiday (try business day)
- API might be temporarily down

### Webhook issues
1. Ensure `WEBHOOK_URL` is accessible from internet
2. Check webhook is set: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
3. For Koyeb, ensure app is running

### Rate limiting
- Implement exponential backoff (already built-in)
- Use caching (enabled by default, 1-hour TTL)

## 🧪 Testing

### Manual Testing Checklist

1. **Basic Commands**
   - `/start` - Should show help
   - `/help` - Should show help
   - `/pair EUR/USD` - Should set pair
   - `/reset` - Should clear pair

2. **Date Formats**
   - `01.02.2020` - European format
   - `2020-02-01` - ISO format
   - `today` - Natural language
   - `2 days ago` - Relative dates

3. **Amount Formats**
   - `100 today` - Simple
   - `1,000.50 today` - US format
   - `1 000,50 today` - European format

4. **Edge Cases**
   - Query without setting pair
   - Invalid date format
   - Invalid currency code
   - Weekend date
   - Future date

## 🔐 Security

- No sensitive data stored
- User IDs only stored locally or in Redis
- API keys not required
- All input validated and sanitized
- Rate limiting on API requests

## 📈 Performance

- **Response Time**: < 2s average
- **Caching**: 1-hour TTL for rates
- **Retry Logic**: Up to 3 attempts with exponential backoff
- **Timeout**: 10 seconds per request
- **Concurrent Requests**: Supported via asyncio

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🔗 Links

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Aiogram Documentation](https://docs.aiogram.dev/)
- [Frankfurter API](https://www.frankfurter.app/)
- [NBU API](https://bank.gov.ua/en/open-data/api-dev)

## 📧 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review logs for error messages
3. Open an issue on GitHub

## 🎯 Roadmap

- [ ] Add more currency pairs
- [ ] Historical rate charts
- [ ] Multi-language support
- [ ] Rate alerts/notifications
- [ ] Currency converter web interface
- [ ] Support for cryptocurrency pairs

## 📊 Changelog

### Version 2.0 (Current)
- ✅ Improved error handling and retry logic
- ✅ Smart input normalization for amounts and dates
- ✅ Comprehensive logging system
- ✅ Optional Redis storage
- ✅ Better validation and user feedback
- ✅ Caching layer for API responses
- ✅ Support for natural language dates
- ✅ Auto-correction for currency code typos

### Version 1.0 (Legacy)
- Basic functionality
- Simple date parsing
- Memory-only storage

---

Made with ❤️ for the Telegram community
