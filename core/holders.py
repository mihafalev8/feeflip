"""Token holder snapshot fetcher for FEEFLIP bot."""

import requests
import json
from dataclasses import dataclass
from typing import List
from utils.logger import setup_logger

logger = setup_logger("feeflip.holders")


@dataclass
class TokenHolder:
    """Represents a token holder with their balance."""

    address: str
    balance: int  # raw token amount (no decimals)
    ui_balance: float  # human-readable balance


class HoldersFetcher:
    """Fetches current token holders from Solana RPC."""

    # Known addresses to exclude from lottery (burn addresses, pools, etc.)
    EXCLUDED_ADDRESSES = {
        "1nc1nerator11111111111111111111111111111111",
        "11111111111111111111111111111111",
    }

    def __init__(self, rpc_url: str, token_mint: str, min_balance: int = 1000):
        self.rpc_url = rpc_url
        self.token_mint = token_mint
        self.min_balance = min_balance

    def get_token_holders(self) -> List[TokenHolder]:
        """
        Fetch all holders of the token using getTokenLargestAccounts
        and getProgramAccounts.

        Returns a list of TokenHolder objects filtered by minimum balance.
        """
        try:
            logger.info("Fetching token holders for %s...", self.token_mint)

            # Use getTokenLargestAccounts for top holders
            holders = self._fetch_largest_accounts()

            # Filter by minimum balance and excluded addresses
            filtered = [
                h
                for h in holders
                if h.balance >= self.min_balance
                and h.address not in self.EXCLUDED_ADDRESSES
            ]

            logger.info(
                "Found %d eligible holders (filtered from %d total, min balance: %d)",
                len(filtered),
                len(holders),
                self.min_balance,
            )
            return filtered

        except Exception as e:
            logger.error("Failed to fetch holders: %s", e)
            return []

    def _fetch_largest_accounts(self) -> List[TokenHolder]:
        """Fetch token largest accounts via Solana RPC."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": [self.token_mint],
        }

        try:
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            data = response.json()

            if "error" in data:
                logger.error("RPC error: %s", data["error"])
                return []

            accounts = data.get("result", {}).get("value", [])
            holders = []

            for account in accounts:
                address = account.get("address", "")
                amount = int(account.get("amount", "0"))
                ui_amount = float(account.get("uiAmount", 0) or 0)

                # Resolve the owner of the token account
                owner = self._get_token_account_owner(address)
                if owner:
                    holders.append(
                        TokenHolder(
                            address=owner,
                            balance=amount,
                            ui_balance=ui_amount,
                        )
                    )

            return holders

        except Exception as e:
            logger.error("Error fetching largest accounts: %s", e)
            return []

    def _get_token_account_owner(self, token_account: str) -> str:
        """Resolve the owner wallet address of a token account."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                token_account,
                {"encoding": "jsonParsed"},
            ],
        }

        try:
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            data = response.json()
            parsed = (
                data.get("result", {})
                .get("value", {})
                .get("data", {})
                .get("parsed", {})
                .get("info", {})
            )
            return parsed.get("owner", "")
        except Exception:
            return ""

    def get_total_supply(self) -> int:
        """Fetch the total supply of the token."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenSupply",
            "params": [self.token_mint],
        }

        try:
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            data = response.json()
            amount = data.get("result", {}).get("value", {}).get("amount", "0")
            return int(amount)
        except Exception as e:
            logger.error("Failed to fetch total supply: %s", e)
            return 0
