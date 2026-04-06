"""Core decision engine for the Occam Logistics bot."""

from __future__ import annotations

from dataclasses import dataclass

from .math_utils import expected_value, kelly_fraction
from .models import MarketSignal, TradeDecision


@dataclass(slots=True)
class RiskConfig:
    bankroll_usd: float = 25.0
    max_position_pct: float = 0.05
    min_ev: float = 0.05
    min_liquidity: float = 1000.0
    kelly_scale: float = 0.25


class DecisionEngine:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def evaluate(self, signal: MarketSignal) -> TradeDecision | None:
        if signal.liquidity < self.config.min_liquidity:
            return None

        ev = expected_value(signal.model_probability, signal.market_price)
        if ev < self.config.min_ev:
            return None

        kelly = kelly_fraction(
            true_probability=signal.model_probability,
            market_price=signal.market_price,
            kelly_scale=self.config.kelly_scale,
        )

        capped_fraction = min(kelly, self.config.max_position_pct)
        if capped_fraction <= 0:
            return None

        size = round(self.config.bankroll_usd * capped_fraction, 2)
        side = "BUY_YES" if signal.model_probability > signal.market_price else "BUY_NO"

        return TradeDecision(
            market_id=signal.market_id,
            side=side,
            size_usd=max(size, 0.5),
            ev=ev,
            kelly_fraction=kelly,
            rationale=(
                f"EV {ev:.2%}, kelly {kelly:.2%}, model {signal.model_probability:.2%}, "
                f"market {signal.market_price:.2%}"
            ),
        )
