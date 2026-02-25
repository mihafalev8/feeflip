"""Telegram notification helper for FEEFLIP bot."""

import aiohttp
from utils.logger import setup_logger

logger = setup_logger("feeflip.telegram")


class TelegramNotifier:
    """Send notifications to a Telegram chat."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        if self.enabled:
            self.base_url = f"https://api.telegram.org/bot{bot_token}"
            logger.info("Telegram notifications enabled for chat %s", chat_id)
        else:
            logger.info("Telegram notifications disabled (no token/chat_id)")

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured Telegram chat."""
        if not self.enabled:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                }
                async with session.post(
                    f"{self.base_url}/sendMessage", json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.debug("Telegram message sent successfully")
                        return True
                    else:
                        body = await resp.text()
                        logger.warning("Telegram API error %d: %s", resp.status, body)
                        return False
        except Exception as e:
            logger.error("Failed to send Telegram message: %s", e)
            return False

    async def announce_winner(
        self,
        winner_address: str,
        jackpot_sol: float,
        winner_balance: int,
        total_supply: int,
        drawing_number: int,
    ) -> bool:
        """Send a formatted winner announcement."""
        win_chance = (winner_balance / total_supply * 100) if total_supply > 0 else 0
        short_addr = f"{winner_address[:6]}...{winner_address[-4:]}"

        message = (
            f"🎰 <b>FEEFLIP JACKPOT #{drawing_number}</b> 🎰\n\n"
            f"🏆 Winner: <code>{short_addr}</code>\n"
            f"💰 Jackpot: <b>{jackpot_sol:.4f} SOL</b>\n"
            f"📊 Win chance was: {win_chance:.2f}%\n"
            f"🪙 Holder balance: {winner_balance:,} tokens\n\n"
            f"💎 Hold more tokens = higher chance to win!\n"
            f"♻️ Next drawing loading..."
        )
        return await self.send_message(message)

    async def announce_fee_claimed(self, amount_sol: float, pool_total: float) -> bool:
        """Announce a fee claim event."""
        message = (
            f"💸 <b>Fees Claimed</b>\n\n"
            f"Claimed: <b>{amount_sol:.4f} SOL</b>\n"
            f"Pool total: <b>{pool_total:.4f} SOL</b>\n"
            f"🎰 Jackpot growing..."
        )
        return await self.send_message(message)
