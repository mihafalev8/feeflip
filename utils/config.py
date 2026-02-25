"""Configuration loader for FEEFLIP bot."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    pumpportal_api_key: str
    token_mint: str
    solana_rpc_url: str
    pool_type: str
    draw_interval_minutes: int
    min_jackpot_sol: float
    min_holder_tokens: int
    sol_reserve: float
    telegram_bot_token: str
    telegram_chat_id: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        api_key = os.getenv("PUMPPORTAL_API_KEY", "")
        token_mint = os.getenv("TOKEN_MINT", "")

        if not api_key:
            raise ValueError("PUMPPORTAL_API_KEY is required. Get one at https://pumpportal.fun/create-wallet")
        if not token_mint:
            raise ValueError("TOKEN_MINT is required. Set your token contract address.")

        return cls(
            pumpportal_api_key=api_key,
            token_mint=token_mint,
            solana_rpc_url=os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"),
            pool_type=os.getenv("POOL_TYPE", "pump"),
            draw_interval_minutes=int(os.getenv("DRAW_INTERVAL_MINUTES", "30")),
            min_jackpot_sol=float(os.getenv("MIN_JACKPOT_SOL", "0.1")),
            min_holder_tokens=int(os.getenv("MIN_HOLDER_TOKENS", "1000")),
            sol_reserve=float(os.getenv("SOL_RESERVE", "0.05")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        )
