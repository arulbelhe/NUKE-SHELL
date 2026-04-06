"""Probability and sizing helpers for prediction-market trading."""

from __future__ import annotations


def expected_value(true_probability: float, market_price: float) -> float:
    """Return EV per $1 stake for a YES contract.

    EV = p*(1-price) - (1-p)*price
    """
    _validate_probability(true_probability, "true_probability")
    _validate_probability(market_price, "market_price")
    return true_probability * (1 - market_price) - (1 - true_probability) * market_price


def kelly_fraction(true_probability: float, market_price: float, kelly_scale: float = 0.25) -> float:
    """Fraction of bankroll to allocate to a position.

    Uses a scaled Kelly approach for binary payout contracts.
    Returns 0 when the edge is non-positive.
    """
    _validate_probability(true_probability, "true_probability")
    _validate_probability(market_price, "market_price")

    b = (1 - market_price) / market_price
    q = 1 - true_probability
    f = (b * true_probability - q) / b
    f = max(0.0, f)
    return f * max(0.0, min(kelly_scale, 1.0))


def _validate_probability(value: float, field_name: str) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be between 0 and 1")
