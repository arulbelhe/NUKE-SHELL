from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MarketSignal:
    market_id: str
    question: str
    market_price: float
    model_probability: float
    liquidity: float
    category: str
    detected_at: datetime


@dataclass(slots=True)
class TradeDecision:
    market_id: str
    side: str
    size_usd: float
    ev: float
    kelly_fraction: float
    rationale: str
