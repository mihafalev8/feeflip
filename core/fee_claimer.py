"""PumpPortal fee claiming logic for FEEFLIP bot."""

import requests
import time
from utils.logger import setup_logger

logger = setup_logger("feeflip.claimer")

PUMPPORTAL_TRADE_URL = "https://pumpportal.fun/api/trade"


class FeeClaimer:
    """Claims creator fees from PumpFun via PumpPortal Lightning API."""

    def __init__(self, api_key: str, pool_type: str = "pump", token_mint: str = ""):
        self.api_key = api_key
        self.pool_type = pool_type
        self.token_mint = token_mint
        self.total_claimed_sol = 0.0
        self.claim_count = 0

    def claim_fees(self) -> dict:
        """
        Claim creator fees from PumpFun.

        For pool_type 'pump': claims all fees at once (no mint needed).
        For pool_type 'meteora-dbc': claims fees for specific token mint.

        Returns:
            dict with keys: 'success' (bool), 'signature' (str), 'error' (str)
        """
        try:
            logger.info(
                "Claiming creator fees from %s pool...", self.pool_type
            )

            payload = {
                "action": "collectCreatorFee",
                "priorityFee": 0.000005,
                "pool": self.pool_type,
            }

            # Meteora DBC requires specifying the mint
            if self.pool_type == "meteora-dbc" and self.token_mint:
                payload["mint"] = self.token_mint

            response = requests.post(
                url=f"{PUMPPORTAL_TRADE_URL}?api-key={self.api_key}",
                data=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                signature = data.get("signature", "")
                if signature:
                    self.claim_count += 1
                    logger.info(
                        "Fee claim #%d successful! TX: https://solscan.io/tx/%s",
                        self.claim_count,
                        signature,
                    )
                    return {"success": True, "signature": signature, "error": ""}
                else:
                    error_msg = str(data.get("errors", data))
                    logger.warning("Fee claim returned no signature: %s", error_msg)
                    return {"success": False, "signature": "", "error": error_msg}
            else:
                logger.warning(
                    "Fee claim failed with status %d: %s",
                    response.status_code,
                    response.text,
                )
                return {
                    "success": False,
                    "signature": "",
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except requests.exceptions.Timeout:
            logger.error("Fee claim request timed out")
            return {"success": False, "signature": "", "error": "Request timed out"}
        except Exception as e:
            logger.error("Fee claim error: %s", e)
            return {"success": False, "signature": "", "error": str(e)}

    def get_stats(self) -> dict:
        """Return claiming statistics."""
        return {
            "total_claimed_sol": self.total_claimed_sol,
            "claim_count": self.claim_count,
            "pool_type": self.pool_type,
        }
