"""Enrollment ramp — gradual batch size increase for outreach campaigns."""

from __future__ import annotations


def calculate_batch_size(total_contacts: int, day_number: int, max_daily: int = 50) -> int:
    """Calculate the batch size for a given day of enrollment.

    Ramp schedule:
        Day 1: 10% of total (or max_daily, whichever is smaller)
        Day 2: 25% of total
        Day 3: 50% of total
        Day 4+: max_daily

    Returns the number of contacts to enroll on this day.
    """
    if total_contacts <= 0 or day_number <= 0:
        return 0

    if day_number == 1:
        pct = 0.10
    elif day_number == 2:
        pct = 0.25
    elif day_number == 3:
        pct = 0.50
    else:
        return min(total_contacts, max_daily)

    batch = int(total_contacts * pct)
    # Always enroll at least 1 if there are contacts
    batch = max(1, batch)
    return min(batch, max_daily)
