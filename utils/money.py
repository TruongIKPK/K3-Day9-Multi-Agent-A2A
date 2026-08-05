"""
Financial Calculation Utility
Rounds BRL monetary values and checks floating point tolerances.
"""

from decimal import Decimal, ROUND_HALF_UP
from core.config import REFUND_ROUND_DIGITS, SPLIT_PAYMENT_TOLERANCE_BRL


def format_brl(value: float) -> float:
    """Rounds float to 2 decimal places using Decimal HALF_UP."""
    d = Decimal(str(value))
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def is_within_split_tolerance(
    total_payment: float,
    total_items: float,
    total_freight: float,
    tolerance: float = SPLIT_PAYMENT_TOLERANCE_BRL
) -> bool:
    """Checks if total payment matches item + freight within tolerance."""
    expected = total_items + total_freight
    diff = abs(total_payment - expected)
    return diff <= tolerance
