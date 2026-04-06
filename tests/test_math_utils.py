from occam_bot.math_utils import expected_value, kelly_fraction


def test_expected_value_positive_edge() -> None:
    ev = expected_value(0.52, 0.35)
    assert round(ev, 3) == 0.17


def test_kelly_zero_for_negative_edge() -> None:
    f = kelly_fraction(0.30, 0.60)
    assert f == 0.0
