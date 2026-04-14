# backtest/engine.py
import vectorbt as vbt
import pandas as pd
import numpy as np
from typing import Dict, Any
from utils.logger import log
from data.manager import DataManager
from strategies.trend_following import TrendFollowing

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.data_manager = DataManager()

    def run_backtest(self, strategy_name: str, symbol: str, start_date: str, end_date: str, strategy_params: dict) -> Dict[str, Any]:
        """Runs a backtest for a given strategy and returns metrics."""
        log.info(f"Running backtest for {strategy_name} on {symbol} from {start_date} to {end_date}")

        # 1. Fetch Data
        data = self.data_manager.get_data(symbol, start_date, end_date, interval="1d")
        if data.empty:
            log.error("Backtest aborted: No data available.")
            return {}

        # 2. Instantiate Strategy and Generate Signals
        if strategy_name == 'TrendFollowing':
            strategy = TrendFollowing(strategy_params)
        else:
            log.error(f"Strategy '{strategy_name}' not found.")
            return {}

        signals_series = strategy.generate_signals(data)

        # Convert 'BUY'/'SELL' to numerical format for vectorbt (-1, 0, 1)
        entries = signals_series == 'BUY'
        exits = signals_series == 'SELL'

        # 3. Run VectorBT Portfolio Simulation
        price = data['close']
        # Create a portfolio from signals
        pf = vbt.Portfolio.from_signals(
            price,
            entries=entries,
            exits=exits,
            init_cash=self.initial_capital,
            fees=self.commission,
            freq='D'
        )

        # 4. Extract Key Metrics
        metrics = {
            'start_value': pf.stats()['Start Value'],
            'end_value': pf.stats()['End Value'],
            'total_return': pf.stats()['Total Return [%]'],
            'max_drawdown': pf.stats()['Max Drawdown [%]'],
            'sharpe_ratio': pf.stats()['Sharpe Ratio'],
            'win_rate': pf.stats()['Win Rate [%]'],
            'total_trades': pf.stats()['Total Trades']
        }
        log.success(f"Backtest complete. Total Return: {metrics['total_return']:.2f}%, Sharpe: {metrics['sharpe_ratio']:.2f}")
        return metrics

if __name__ == '__main__':
    # Example Usage
    engine = BacktestEngine()
    results = engine.run_backtest(
        strategy_name='TrendFollowing',
        symbol='AAPL',
        start_date='2020-01-01',
        end_date='2023-12-31',
        strategy_params={'fast_ma': 20, 'slow_ma': 50}
    )
    print(results)