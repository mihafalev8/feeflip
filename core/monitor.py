"""WebSocket trade monitor for FEEFLIP bot via PumpPortal."""

import asyncio
import json
import websockets
from utils.logger import setup_logger

logger = setup_logger("feeflip.monitor")

PUMPPORTAL_WS = "wss://pumpportal.fun/api/data"


class TradeMonitor:
    """
    Monitors real-time trading activity on a token via PumpPortal WebSocket.

    Tracks trade count, volume, and provides callbacks for trade events.
    """

    def __init__(self, token_mint: str):
        self.token_mint = token_mint
        self.trade_count = 0
        self.total_volume_sol = 0.0
        self.buy_count = 0
        self.sell_count = 0
        self.running = False
        self._callbacks = []

    def on_trade(self, callback):
        """Register a callback for trade events."""
        self._callbacks.append(callback)

    async def start(self):
        """Start monitoring trades via WebSocket."""
        self.running = True
        logger.info("Starting trade monitor for %s...", self.token_mint)

        while self.running:
            try:
                async with websockets.connect(PUMPPORTAL_WS) as ws:
                    # Subscribe to token trades
                    subscribe_msg = {
                        "method": "subscribeTokenTrade",
                        "keys": [self.token_mint],
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    logger.info("Subscribed to trades for %s", self.token_mint)

                    async for message in ws:
                        if not self.running:
                            break

                        try:
                            trade = json.loads(message)
                            await self._process_trade(trade)
                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON from WebSocket")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("WebSocket error: %s, reconnecting in 10s...", e)
                await asyncio.sleep(10)

    async def _process_trade(self, trade: dict):
        """Process a single trade event."""
        self.trade_count += 1

        trade_type = trade.get("txType", "unknown")
        sol_amount = float(trade.get("solAmount", 0)) / 1e9  # lamports to SOL

        self.total_volume_sol += sol_amount

        if trade_type == "buy":
            self.buy_count += 1
        elif trade_type == "sell":
            self.sell_count += 1

        logger.debug(
            "Trade #%d: %s %.4f SOL | Total volume: %.4f SOL",
            self.trade_count,
            trade_type.upper(),
            sol_amount,
            self.total_volume_sol,
        )

        # Notify callbacks
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(trade)
                else:
                    callback(trade)
            except Exception as e:
                logger.error("Trade callback error: %s", e)

    def stop(self):
        """Stop the trade monitor."""
        self.running = False
        logger.info("Trade monitor stopped")

    def get_stats(self) -> dict:
        """Return monitoring statistics."""
        return {
            "trade_count": self.trade_count,
            "total_volume_sol": self.total_volume_sol,
            "buy_count": self.buy_count,
            "sell_count": self.sell_count,
            "buy_sell_ratio": (
                self.buy_count / self.sell_count if self.sell_count > 0 else float("inf")
            ),
        }
