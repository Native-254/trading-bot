# strategies/trend_following.py
import pandas as pd
import numpy as np
import ta
from strategies.base import BaseStrategy
from utils.logger import log
import ta.trend
import ta.momentum

class TrendFollowing(BaseStrategy):
    """
    A simple trend-following strategy using Moving Averages and RSI.
    BUY when 50MA > 200MA and RSI < 30 (oversold).
    SELL when 50MA < 200MA or RSI > 70 (overbought).
    """
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if data.empty or 'close' not in data.columns:
            return pd.Series(index=data.index, dtype='object')

        df = data.copy()
        fast_ma = self.parameters.get('fast_ma', 50)
        slow_ma = self.parameters.get('slow_ma', 200)
        rsi_period = self.parameters.get('rsi_period', 14)
        rsi_oversold = self.parameters.get('rsi_oversold', 30)
        rsi_overbought = self.parameters.get('rsi_overbought', 70)

        # Calculate indicators
        df['ma_fast'] = ta.trend.sma_indicator(df['close'], window=fast_ma)
        df['ma_slow'] = ta.trend.sma_indicator(df['close'], window=slow_ma)
        df['rsi'] = ta.momentum.rsi(df['close'], window=rsi_period)

        # Generate signals
        signals = pd.Series(index=df.index, dtype='object')
        signals[:] = 'HOLD'

        # Buy condition: Golden Cross & Oversold RSI
        buy_condition = (df['ma_fast'] > df['ma_slow']) & (df['rsi'] < rsi_oversold)
        signals[buy_condition] = 'BUY'

        # Sell condition: Death Cross or Overbought RSI
        sell_condition = (df['ma_fast'] < df['ma_slow']) | (df['rsi'] > rsi_overbought)
        signals[sell_condition] = 'SELL'

        log.debug(f"Generated {signals.value_counts().to_dict()} for {data.index[-1]}")
        return signals