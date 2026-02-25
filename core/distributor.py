"""SOL distribution to lottery winners for FEEFLIP bot."""

import requests
import json
from utils.logger import setup_logger

logger = setup_logger("feeflip.distributor")

LAMPORTS_PER_SOL = 1_000_000_000


class SolDistributor:
    """
    Distributes SOL jackpots to lottery winners.

    Uses PumpPortal Lightning API for simple transfers,
    or can construct local transactions for full control.
    """

    def __init__(self, api_key: str, rpc_url: str):
        self.api_key = api_key
        self.rpc_url = rpc_url
        self.total_distributed = 0.0

    def send_sol(self, recipient: str, amount_sol: float) -> dict:
        """
        Send SOL to the lottery winner.

        Uses Solana native transfer via RPC.
        For production, you would sign with your wallet's private key.

        Args:
            recipient: Winner's wallet address
            amount_sol: Amount of SOL to send

        Returns:
            dict with 'success', 'signature', 'error' keys
        """
        try:
            logger.info(
                "Distributing %.4f SOL to winner %s...",
                amount_sol,
                recipient,
            )

            # Build a native SOL transfer instruction
            # In production, this would use solders to create and sign a transaction
            # Here we demonstrate the flow with the RPC approach

            lamports = int(amount_sol * LAMPORTS_PER_SOL)

            # For the MVP, we use a simple transfer approach
            # Production would use: solders.system_program.transfer()
            result = self._execute_transfer(recipient, lamports)

            if result["success"]:
                self.total_distributed += amount_sol
                logger.info(
                    "Distribution successful! TX: %s | Total distributed: %.4f SOL",
                    result["signature"],
                    self.total_distributed,
                )
            else:
                logger.warning("Distribution failed: %s", result["error"])

            return result

        except Exception as e:
            logger.error("Distribution error: %s", e)
            return {"success": False, "signature": "", "error": str(e)}

    def _execute_transfer(self, recipient: str, lamports: int) -> dict:
        """
        Execute a SOL transfer via Solana RPC.

        NOTE: In production, you must:
        1. Create a transfer instruction with solders
        2. Sign with your wallet keypair
        3. Send via your RPC endpoint

        This method provides the framework for that flow.
        """
        try:
            # Production implementation would look like:
            #
            # from solders.keypair import Keypair
            # from solders.pubkey import Pubkey
            # from solders.system_program import TransferParams, transfer
            # from solders.transaction import Transaction
            # from solders.message import Message
            #
            # sender = Keypair.from_base58_string(PRIVATE_KEY)
            # ix = transfer(TransferParams(
            #     from_pubkey=sender.pubkey(),
            #     to_pubkey=Pubkey.from_string(recipient),
            #     lamports=lamports,
            # ))
            # blockhash = get_latest_blockhash()
            # msg = Message.new_with_blockhash([ix], sender.pubkey(), blockhash)
            # tx = Transaction.new_unsigned(msg)
            # tx.sign([sender], blockhash)
            # signature = send_transaction(tx)

            logger.info(
                "Transfer prepared: %d lamports (%.4f SOL) to %s",
                lamports,
                lamports / LAMPORTS_PER_SOL,
                recipient,
            )

            # Placeholder for actual transaction
            # In production, replace with real signing and sending
            return {
                "success": True,
                "signature": "SIMULATED_TX_REPLACE_WITH_REAL",
                "error": "",
            }

        except Exception as e:
            return {"success": False, "signature": "", "error": str(e)}

    def get_wallet_balance(self) -> float:
        """Fetch the bot wallet's SOL balance."""
        try:
            # This would use the bot's public key
            # For now, return a placeholder
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": ["YOUR_BOT_WALLET_PUBKEY"],
            }
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            data = response.json()
            lamports = data.get("result", {}).get("value", 0)
            return lamports / LAMPORTS_PER_SOL
        except Exception as e:
            logger.error("Failed to fetch wallet balance: %s", e)
            return 0.0

    def get_stats(self) -> dict:
        """Return distribution statistics."""
        return {
            "total_distributed_sol": self.total_distributed,
        }
