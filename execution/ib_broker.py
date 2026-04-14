# execution/ib_broker.py
import asyncio
from ib_async import IB, Stock, MarketOrder, LimitOrder, util
from typing import Dict, Any, List
from utils.config import CONFIG
from utils.logger import log
from execution.broker import Broker

class IBBroker(Broker):
    def __init__(self):
        self.ib = IB()
        self.config = CONFIG['exchanges']['nyse']
        self.connected = False

    def connect(self):
        """Connects to TWS or IB Gateway."""
        if self.connected:
            return
        try:
            self.ib.connect(
                host='127.0.0.1',
                port=self.config['port'],
                clientId=self.config['client_id'],
                account=self.config['account_id']
            )
            self.connected = True
            log.success(f"Connected to IBKR. Account: {self.config['account_id']}")
        except Exception as e:
            log.error(f"Failed to connect to IBKR: {e}")
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """Fetches account summary."""
        if not self.connected: self.connect()
        account_values = self.ib.accountValues(self.config['account_id'])
        net_liquidation = next((float(v.value) for v in account_values if v.tag == 'NetLiquidation'), 0.0)
        return {'net_liquidation': net_liquidation, 'account': self.config['account_id']}

    def place_order(self, symbol: str, side: str, quantity: int, order_type: str = 'MKT', limit_price: float = None, stop_price: float = None) -> Dict[str, Any]:
        """Places an order with IBKR."""
        if not self.connected: self.connect()

        # Create a contract for US stocks
        contract = Stock(symbol, 'SMART', 'USD')
        self.ib.qualifyContracts(contract)

        # Create order object
        if order_type.upper() == 'MKT':
            order = MarketOrder(side.upper(), quantity)
        elif order_type.upper() == 'LMT':
            if limit_price is None:
                raise ValueError("Limit price required for LMT order")
            order = LimitOrder(side.upper(), quantity, limit_price)
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        # Place the order
        trade = self.ib.placeOrder(contract, order)
        log.info(f"Order placed: {side} {quantity} {symbol} @ {order_type}. ID: {trade.order.orderId}")

        # Wait for order to be submitted
        self.ib.sleep(1)
        return {
            'order_id': trade.order.orderId,
            'status': trade.orderStatus.status,
            'filled_quantity': trade.orderStatus.filled,
            'avg_price': trade.orderStatus.avgFillPrice
        }

    def cancel_order(self, order_id: str) -> bool:
        """Cancels an order by ID."""
        if not self.connected: self.connect()
        for trade in self.ib.trades():
            if str(trade.order.orderId) == str(order_id):
                self.ib.cancelOrder(trade.order)
                log.info(f"Order {order_id} cancelled.")
                return True
        log.warning(f"Order {order_id} not found.")
        return False

    def get_positions(self) -> list:
        """Returns a list of current positions."""
        if not self.connected: self.connect()
        positions = []
        for pos in self.ib.positions():
            positions.append({
                'symbol': pos.contract.symbol,
                'quantity': pos.position,
                'avg_cost': pos.avgCost,
                'market_value': pos.marketValue
            })
        return positions

    def disconnect(self):
        """Cleanly disconnect."""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            log.info("Disconnected from IBKR.")