"""
FEEFLIP — PumpFun Creator Fee Lottery Bot

Transforms PumpFun creator fees into a weighted lottery jackpot
for token holders on Solana.

Usage:
    python feeflip.py
"""

import asyncio
import time
import signal
import sys

from utils.config import Config
from utils.logger import setup_logger
from utils.telegram import TelegramNotifier
from core.fee_claimer import FeeClaimer
from core.lottery import LotteryEngine
from core.holders import HoldersFetcher
from core.distributor import SolDistributor
from core.monitor import TradeMonitor

logger = setup_logger("feeflip")

BANNER = r"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🎰  FEEFLIP — Creator Fee Lottery Bot  🎰            ║
║                                                           ║
║     Turn PumpFun creator fees into jackpots               ║
║     for your token holders!                               ║
║                                                           ║
║     More tokens = Higher chance to win                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""


class FeeFlipBot:
    """Main bot orchestrator for the FEEFLIP lottery system."""

    def __init__(self, config: Config):
        self.config = config
        self.running = False

        # Initialize components
        self.claimer = FeeClaimer(
            api_key=config.pumpportal_api_key,
            pool_type=config.pool_type,
            token_mint=config.token_mint,
        )
        self.lottery = LotteryEngine()
        self.holders_fetcher = HoldersFetcher(
            rpc_url=config.solana_rpc_url,
            token_mint=config.token_mint,
            min_balance=config.min_holder_tokens,
        )
        self.distributor = SolDistributor(
            api_key=config.pumpportal_api_key,
            rpc_url=config.solana_rpc_url,
        )
        self.monitor = TradeMonitor(token_mint=config.token_mint)
        self.telegram = TelegramNotifier(
            bot_token=config.telegram_bot_token,
            chat_id=config.telegram_chat_id,
        )

        logger.info("FeeFlip bot initialized")
        logger.info("Token: %s", config.token_mint)
        logger.info("Pool type: %s", config.pool_type)
        logger.info("Draw interval: %d minutes", config.draw_interval_minutes)
        logger.info("Min jackpot: %.4f SOL", config.min_jackpot_sol)
        logger.info("Min holder balance: %d tokens", config.min_holder_tokens)

    async def run(self):
        """Start the bot main loop."""
        self.running = True
        logger.info("Starting FeeFlip bot...")

        # Start trade monitor in background
        monitor_task = asyncio.create_task(self.monitor.start())

        # Main lottery loop
        lottery_task = asyncio.create_task(self._lottery_loop())

        try:
            await asyncio.gather(monitor_task, lottery_task)
        except asyncio.CancelledError:
            logger.info("Bot tasks cancelled")
        finally:
            self.running = False
            self.monitor.stop()

    async def _lottery_loop(self):
        """Main loop: claim fees, check pool, run drawings."""
        logger.info("Lottery loop started. First claim in 10 seconds...")
        await asyncio.sleep(10)

        while self.running:
            try:
                # Step 1: Claim creator fees
                await self._claim_and_add_to_pool()

                # Step 2: Wait for transaction to settle
                await asyncio.sleep(3)

                # Step 3: Check if we should run a drawing
                if self.lottery.should_draw(
                    min_jackpot=self.config.min_jackpot_sol,
                    interval_minutes=self.config.draw_interval_minutes,
                ):
                    await self._run_drawing()

                # Step 4: Print status
                self._print_status()

                # Step 5: Wait for next cycle
                wait_time = self.config.draw_interval_minutes * 60
                logger.info("Next cycle in %d minutes...", self.config.draw_interval_minutes)
                await asyncio.sleep(wait_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Lottery loop error: %s", e)
                await asyncio.sleep(30)

    async def _claim_and_add_to_pool(self):
        """Claim creator fees and add to lottery pool."""
        result = self.claimer.claim_fees()

        if result["success"]:
            # In production, you would check the actual SOL received
            # by comparing wallet balance before and after the claim.
            # For now, we estimate based on the transaction.
            balance = self.distributor.get_wallet_balance()
            available = max(0, balance - self.config.sol_reserve)

            if available > 0:
                self.lottery.add_to_pool(available)
                await self.telegram.announce_fee_claimed(
                    available, self.lottery.get_pool_balance()
                )
                logger.info("Added %.4f SOL to lottery pool", available)
        else:
            logger.info("No fees to claim or claim failed: %s", result.get("error", ""))

    async def _run_drawing(self):
        """Execute a lottery drawing."""
        logger.info("=" * 60)
        logger.info("LOTTERY DRAWING STARTING!")
        logger.info("=" * 60)

        # Fetch current holders
        holders = self.holders_fetcher.get_token_holders()
        if not holders:
            logger.warning("No eligible holders found, skipping drawing")
            return

        total_supply = self.holders_fetcher.get_total_supply()

        # Run the drawing
        result = self.lottery.draw(holders, total_supply)
        if not result:
            logger.warning("Drawing failed")
            return

        # Distribute jackpot to winner
        dist_result = self.distributor.send_sol(
            recipient=result.winner_address,
            amount_sol=result.jackpot_sol,
        )

        if dist_result["success"]:
            logger.info("=" * 60)
            logger.info("WINNER: %s", result.winner_address)
            logger.info("JACKPOT: %.4f SOL", result.jackpot_sol)
            logger.info("WIN PROBABILITY: %.2f%%", result.win_probability * 100)
            logger.info("PARTICIPANTS: %d", result.total_participants)
            logger.info("TX: %s", dist_result["signature"])
            logger.info("=" * 60)

            # Announce on Telegram
            await self.telegram.announce_winner(
                winner_address=result.winner_address,
                jackpot_sol=result.jackpot_sol,
                winner_balance=result.winner_balance,
                total_supply=total_supply,
                drawing_number=result.drawing_number,
            )
        else:
            logger.error(
                "Failed to distribute jackpot: %s", dist_result["error"]
            )

    def _print_status(self):
        """Print current bot status."""
        lottery_stats = self.lottery.get_stats()
        monitor_stats = self.monitor.get_stats()

        logger.info("--- STATUS ---")
        logger.info("Pool: %.4f SOL", lottery_stats["current_pool_sol"])
        logger.info("Total drawings: %d", lottery_stats["total_drawings"])
        logger.info("Total distributed: %.4f SOL", lottery_stats["total_distributed_sol"])
        logger.info("Biggest jackpot: %.4f SOL", lottery_stats["biggest_jackpot_sol"])
        logger.info("Unique winners: %d", len(lottery_stats.get("unique_winners", [])))
        logger.info("Trades monitored: %d", monitor_stats["trade_count"])
        logger.info("Volume: %.4f SOL", monitor_stats["total_volume_sol"])
        logger.info("--------------")

    def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping FeeFlip bot...")
        self.running = False
        self.monitor.stop()


def main():
    """Entry point for the FEEFLIP bot."""
    print(BANNER)

    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    bot = FeeFlipBot(config)

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        bot.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the bot
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
