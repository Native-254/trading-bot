# Mkopo Trading Bot

A fully automated, risk‑managed trading bot for the **NYSE** (via Interactive Brokers) with paper‑trading support, Discord/Telegram alerts, and a modular strategy engine. Built from scratch in Python.

![Bot Status](https://img.shields.io/badge/status-paper_trading-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

## ✨ Features

- **Multi‑strategy engine** – currently includes a Trend‑Following (MA crossover + RSI) strategy; easy to add more.
- **Interactive Brokers integration** – paper & live trading via `ib_async`.
- **Full risk management** – position sizing (ATR‑based), max portfolio heat, daily loss limits, drawdown protection.
- **Data pipeline** – Yahoo Finance historical data with local Parquet caching and rate‑limit handling.
- **Notifications** – real‑time alerts to Discord (embeds) and Telegram.
- **Backtesting** – vectorized backtesting with `vectorbt` for strategy validation.
- **Headless operation** – runs 24/7 on a VPS or local machine.
- **Modular design** – easy to swap data providers, brokers, or strategies.
- **Paper‑trading first** – built‑in simulation mode for safe testing.

## 🏗️ Architecture
trading_bot/
├── config/ # YAML configuration & templates
├── data/ # Data providers, manager & cache
├── strategies/ # Strategy classes (base + implementations)
├── backtest/ # Backtesting engine (vectorbt)
├── execution/ # Broker abstraction & IBKR implementation
├── risk/ # Risk manager (position sizing, limits)
├── monitoring/ # Discord & Telegram alerters, health API
├── live/ # Main trading engine (orchestrator)
├── utils/ # Config loader, logger
├── logs/ # Runtime logs
├── data/raw/ # Parquet cache
├── requirements.txt # Python dependencies
└── README.md


## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Interactive Brokers Gateway (or TWS) with paper trading account
- (Optional) Discord webhook / Telegram bot for alerts

### Installation

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading-bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
Configuration

Copy the settings template and edit it:

bash
cp config/settings.yaml.template config/settings.yaml
nano config/settings.yaml   # Set broker port, account, etc.
Create a .env file for secrets (never commit):

bash
echo "IB_ACCOUNT_ID=DU123456" >> .env
echo "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/..." >> .env
echo "TELEGRAM_BOT_TOKEN=..." >> .env
echo "TELEGRAM_CHAT_ID=..." >> .env
Run in Paper Trading Mode
Start IB Gateway (paper trading) with API enabled (port 4002).

Launch the bot:

bash
python live/engine.py
Watch the terminal logs and your Discord/Telegram for trade alerts.

Note: By default, the bot runs the main iteration every hour. To change the schedule, edit live/engine.py (look for schedule.every).

## 📊 Strategies
TrendFollowing (default)
Uses moving averages (fast/slow) and RSI to generate signals:

BUY when fast_MA > slow_MA and RSI < oversold

SELL when fast_MA < slow_MA or RSI > overbought

Parameters adjustable in config/settings.yaml.

Adding Your Own
Create a new class extending BaseStrategy in strategies/.

Implement generate_signals(data).

Register it in live/engine.py.

## 🛡️ Risk Management
The bot enforces strict risk rules before every trade:

Max capital per trade: 2% of equity (configurable)

Max portfolio heat: 15% total open risk

Daily loss limit: stop trading if -5% on the day

Max drawdown: reduce position sizes by 50% after 20% drawdown

ATR‑based stops: dynamic stop‑losses using Average True Range

All values can be adjusted in config/settings.yaml.

## 🔔 Notifications
Discord
Rich embeds with trade details (symbol, action, quantity, price) and error alerts. Set up via webhook URL in .env.

Telegram
Plain text alerts. Requires a bot token and chat ID (obtain via @BotFather).

Both can be enabled/disabled independently in the config.

## 🧪 Backtesting
To evaluate a strategy before live use:

python
from backtest.engine import BacktestEngine
engine = BacktestEngine()
results = engine.run_backtest(
    strategy_name='TrendFollowing',
    symbol='AAPL',
    start_date='2020-01-01',
    end_date='2024-01-01',
    strategy_params={'fast_ma': 20, 'slow_ma': 50}
)
print(results)
Uses vectorbt for fast, vectorized simulation.

## ☁️ 24/7 Deployment (VPS)
The bot can run unattended on a free‑tier Oracle Cloud, Google Cloud, or AWS instance.

Recommended: Oracle Cloud Always Free (4 ARM cores, 24 GB RAM).

Steps:

Provision an Ubuntu VM.

Clone the repo, install dependencies, add config files.

Run as a systemd service for auto‑start and crash recovery.

A sample service file is provided in the Wiki.

## 📜 License
MIT – use, modify, and distribute freely.

⚠️ Disclaimer
This bot is for educational purposes. Use at your own risk. Past performance does not guarantee future results. Always test thoroughly in paper trading before committing real capital.


---
]
- [[Troubleshooting & FAQ]]
