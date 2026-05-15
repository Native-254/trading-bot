from monitoring.telegram_alerter import TelegramAlerter
from utils.config import CONFIG

token = CONFIG['monitoring']['telegram']['bot_token']
print(f"DEBUG: Bot token starts with: {token[:10]}... (length: {len(token)})")
print(f"DEBUG: Chat ID: {CONFIG['monitoring']['telegram']['chat_id']}")

alerter = TelegramAlerter()
alerter.send_message("✅ Telegram integration test from Mkopo Bot is successful!")
alerter.send_trade_alert("TEST", "BUY", 10, 99.99)
print("Telegram test messages sent.")
