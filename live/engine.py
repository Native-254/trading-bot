# live/engine.py
import time
import schedule
import pandas as pd
from datetime import datetime, timedelta
from typing import List

from utils.config import CONFIG
from utils.logger import log
from data.manager import DataManager
from strategies.trend_following import TrendFollowing
from risk.manager import RiskManager
from execution.ib_broker import IBBroker
from monitoring.telegram_alerter import TelegramAlerter

class TradingEngine:
    def __init__(self):
        log.info("Initializing Trading Engine...")
        self.config = CONFIG
        self.data_manager = DataManager()
        self.broker = IBBroker()
        self.telegram = TelegramAlerter()

        # Initialize with paper trading account value
        initial_capital = self.broker.get_account_info()['net_liquidation']
        self.risk_manager = RiskManager(initial_capital)

        self.strategies = []
        for strat_config in self.config['strategies']['active']:
            if strat_config['enabled']:
                if strat_config['name'] == 'TrendFollowing':
                    params = self.config['strategies']['parameters']['trend_following']
                    self.strategies.append(TrendFollowing(params))
                # Add other strategies here

        self.symbols_to_trade = ['AAPL', 'MSFT', 'GOOGL'] # Your watchlist
        self.is_running = False
        log.success("Trading Engine initialized.")

    def run_iteration(self):
        """Single iteration of the main trading loop."""
        log.info(f"--- Running iteration at {datetime.now()} ---")

        # 1. Update Risk Manager with current capital
        account_info = self.broker.get_account_info()
        current_capital = account_info['net_liquidation']
        # Simplified P&L calculation for the loop
        pnl_change = current_capital - self.risk_manager.current_capital
        self.risk_manager.update_portfolio(pnl_change, 0) # 0 open_risk_change for now

        if not self.risk_manager.can_trade():
            log.warning("Trading halted by risk manager.")
            return

        # 2. For each symbol, generate signals
        for symbol in self.symbols_to_trade:
            try:
                # Fetch recent data (e.g., last 200 days)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=200)
                df = self.data_manager.get_data(symbol,
                                                start_date.strftime('%Y-%m-%d'),
                                                end_date.strftime('%Y-%m-%d'),
                                                interval="1d")

                if df.empty:
                    continue

                # 3. Run strategies
                for strategy in self.strategies:
                    signals = strategy.generate_signals(df)
                    latest_signal = signals.iloc[-1]

                    if latest_signal != 'HOLD':
                        log.info(f"Signal detected for {symbol}: {latest_signal} by {strategy.name}")

                        # 4. Calculate trade details
                        last_price = df['close'].iloc[-1]
                        # Simple ATR for stop-loss (using last 14 periods)
                        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
                        stop_loss = last_price - (atr * self.config['risk_management']['volatility_stop_multiplier']) if latest_signal == 'BUY' else last_price + (atr * self.config['risk_management']['volatility_stop_multiplier'])

                        # 5. Calculate position size
                        quantity = strategy.calculate_position_size(
                            capital=current_capital,
                            risk_per_trade=self.config['risk_management']['max_capital_per_trade'],
                            entry_price=last_price,
                            stop_loss_price=stop_loss
                        )
                        if quantity == 0:
                            log.warning(f"Position size for {symbol} is zero. Skipping.")
                            continue

                        # 6. Validate with Risk Manager
                        order_valid, msg = self.risk_manager.validate_order(
                            symbol, latest_signal, quantity, last_price, stop_loss
                        )
                        if not order_valid:
                            log.warning(f"Order rejected for {symbol}: {msg}")
                            continue

                        # 7. Execute Trade (Paper or Live)
                        if self.config['execution']['paper_trading']:
                            log.success(f"[PAPER] Would {latest_signal} {quantity} shares of {symbol} at {last_price:.2f}. Stop: {stop_loss:.2f}")
                            # Simulate an order for risk manager
                            trade_risk = quantity * abs(last_price - stop_loss)
                            self.risk_manager.update_portfolio(0, trade_risk) # P&L change 0 for now
                            self.telegram.send_trade_alert(symbol, latest_signal, quantity, last_price)
                        else:
                            # --- LIVE TRADING ---
                            try:
                                self.broker.connect()
                                order_result = self.broker.place_order(
                                    symbol=symbol,
                                    side=latest_signal,
                                    quantity=quantity,
                                    order_type='MKT'
                                )
                                if order_result and order_result['status'] == 'Filled':
                                    # Update risk manager with the actual trade
                                    trade_risk = quantity * abs(last_price - stop_loss)
                                    self.risk_manager.update_portfolio(0, trade_risk)
                                    self.telegram.send_trade_alert(symbol, latest_signal, quantity, order_result['avg_price'])
                                    log.success(f"LIVE ORDER EXECUTED: {order_result}")
                                else:
                                    log.error(f"Live order failed for {symbol}. Status: {order_result}")
                                    self.telegram.send_error_alert(f"Live order failed for {symbol}.")
                            except Exception as e:
                                log.exception(f"Critical error placing live order for {symbol}: {e}")
                                self.telegram.send_error_alert(f"Live order exception for {symbol}: {e}")
                            finally:
                                self.broker.disconnect()

            except Exception as e:
                log.error(f"Error processing {symbol}: {e}")
                self.telegram.send_error_alert(f"Error processing {symbol}: {e}")

    def start(self):
        """Starts the main trading loop."""
        self.is_running = True
        log.info(f"Starting {self.config['general']['bot_name']} Trading Bot...")

        # Schedule the main loop to run daily at a specific time (e.g., after market close)
        # For intraday, you'd schedule it more frequently.
        schedule.every().day.at("16:30").do(self.run_iteration) # 4:30 PM EST, after NYSE close

        # Schedule a daily reset for the risk manager's P&L
        schedule.every().day.at("00:01").do(self.risk_manager.reset_daily_pnl)

        # Run the main loop
        while self.is_running:
            schedule.run_pending()
            time.sleep(30) # Check every 30 seconds

        log.info("Trading bot stopped.")

if __name__ == "__main__":
    engine = TradingEngine()
    try:
        engine.start()
    except KeyboardInterrupt:
        log.info("Shutdown signal received. Stopping bot...")
        engine.is_running = False