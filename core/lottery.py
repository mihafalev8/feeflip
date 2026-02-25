"""Weighted lottery engine for FEEFLIP bot."""

import random
import time
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional
from core.holders import TokenHolder
from utils.logger import setup_logger

logger = setup_logger("feeflip.lottery")

STATS_FILE = "feeflip_stats.json"


@dataclass
class DrawingResult:
    """Result of a single lottery drawing."""

    drawing_number: int
    winner_address: str
    winner_balance: int
    jackpot_sol: float
    total_participants: int
    total_supply: int
    win_probability: float
    timestamp: float


@dataclass
class LotteryStats:
    """Cumulative lottery statistics."""

    total_drawings: int = 0
    total_distributed_sol: float = 0.0
    biggest_jackpot_sol: float = 0.0
    unique_winners: set = field(default_factory=set)
    last_drawing_time: float = 0.0
    history: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_drawings": self.total_drawings,
            "total_distributed_sol": self.total_distributed_sol,
            "biggest_jackpot_sol": self.biggest_jackpot_sol,
            "unique_winners": list(self.unique_winners),
            "last_drawing_time": self.last_drawing_time,
            "history": self.history[-50:],  # keep last 50 drawings
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LotteryStats":
        stats = cls()
        stats.total_drawings = data.get("total_drawings", 0)
        stats.total_distributed_sol = data.get("total_distributed_sol", 0.0)
        stats.biggest_jackpot_sol = data.get("biggest_jackpot_sol", 0.0)
        stats.unique_winners = set(data.get("unique_winners", []))
        stats.last_drawing_time = data.get("last_drawing_time", 0.0)
        stats.history = data.get("history", [])
        return stats


class LotteryEngine:
    """
    Weighted lottery engine.

    Selects a random winner from token holders, weighted by their balance.
    More tokens = higher probability of winning.
    """

    def __init__(self):
        self.pool_sol = 0.0
        self.stats = self._load_stats()
        logger.info(
            "Lottery engine initialized. Previous drawings: %d, Total distributed: %.4f SOL",
            self.stats.total_drawings,
            self.stats.total_distributed_sol,
        )

    def add_to_pool(self, amount_sol: float):
        """Add SOL to the lottery pool."""
        self.pool_sol += amount_sol
        logger.info(
            "Added %.4f SOL to pool. Pool total: %.4f SOL",
            amount_sol,
            self.pool_sol,
        )

    def should_draw(self, min_jackpot: float, interval_minutes: int) -> bool:
        """Check if conditions are met for a drawing."""
        if self.pool_sol < min_jackpot:
            logger.debug(
                "Pool (%.4f SOL) below minimum (%.4f SOL), skipping draw",
                self.pool_sol,
                min_jackpot,
            )
            return False

        if self.stats.last_drawing_time > 0:
            elapsed = time.time() - self.stats.last_drawing_time
            if elapsed < interval_minutes * 60:
                remaining = interval_minutes * 60 - elapsed
                logger.debug("Next drawing in %.0f seconds", remaining)
                return False

        return True

    def draw(
        self, holders: List[TokenHolder], total_supply: int
    ) -> Optional[DrawingResult]:
        """
        Perform a weighted random drawing.

        Each holder's chance of winning is proportional to their token balance:
            P(win) = holder_balance / sum_of_all_eligible_balances

        Args:
            holders: List of eligible token holders
            total_supply: Total token supply for probability calculation

        Returns:
            DrawingResult if successful, None if no eligible holders
        """
        if not holders:
            logger.warning("No eligible holders for drawing")
            return None

        if self.pool_sol <= 0:
            logger.warning("Pool is empty, cannot draw")
            return None

        # Build weighted list
        weights = [h.balance for h in holders]
        total_weight = sum(weights)

        if total_weight == 0:
            logger.warning("Total weight is zero, cannot draw")
            return None

        # Weighted random selection
        winner = random.choices(holders, weights=weights, k=1)[0]

        # Calculate win probability
        win_probability = winner.balance / total_weight if total_weight > 0 else 0

        # Create result
        jackpot = self.pool_sol
        self.stats.total_drawings += 1
        drawing_number = self.stats.total_drawings

        result = DrawingResult(
            drawing_number=drawing_number,
            winner_address=winner.address,
            winner_balance=winner.balance,
            jackpot_sol=jackpot,
            total_participants=len(holders),
            total_supply=total_supply,
            win_probability=win_probability,
            timestamp=time.time(),
        )

        # Update stats
        self.stats.total_distributed_sol += jackpot
        self.stats.biggest_jackpot_sol = max(
            self.stats.biggest_jackpot_sol, jackpot
        )
        self.stats.unique_winners.add(winner.address)
        self.stats.last_drawing_time = time.time()
        self.stats.history.append(
            {
                "drawing": drawing_number,
                "winner": winner.address,
                "jackpot": jackpot,
                "participants": len(holders),
                "probability": win_probability,
                "timestamp": result.timestamp,
            }
        )

        # Reset pool
        self.pool_sol = 0.0

        # Save stats
        self._save_stats()

        logger.info(
            "DRAWING #%d COMPLETE! Winner: %s | Jackpot: %.4f SOL | "
            "Probability: %.2f%% | Participants: %d",
            drawing_number,
            winner.address,
            jackpot,
            win_probability * 100,
            len(holders),
        )

        return result

    def get_pool_balance(self) -> float:
        """Return current pool balance."""
        return self.pool_sol

    def get_stats(self) -> dict:
        """Return lottery statistics."""
        return {
            **self.stats.to_dict(),
            "current_pool_sol": self.pool_sol,
        }

    def _save_stats(self):
        """Persist stats to disk."""
        try:
            with open(STATS_FILE, "w") as f:
                json.dump(self.stats.to_dict(), f, indent=2)
        except Exception as e:
            logger.error("Failed to save stats: %s", e)

    def _load_stats(self) -> LotteryStats:
        """Load stats from disk."""
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f:
                    data = json.load(f)
                return LotteryStats.from_dict(data)
        except Exception as e:
            logger.error("Failed to load stats: %s", e)
        return LotteryStats()
