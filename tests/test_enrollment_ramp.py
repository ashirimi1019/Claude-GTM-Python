"""Tests for services/enrollment_ramp.py."""

from services.enrollment_ramp import calculate_batch_size


class TestCalculateBatchSize:
    def test_day_1_is_10_percent(self):
        assert calculate_batch_size(100, 1) == 10

    def test_day_2_is_25_percent(self):
        assert calculate_batch_size(100, 2) == 25

    def test_day_3_is_50_percent(self):
        assert calculate_batch_size(100, 3) == 50

    def test_day_4_plus_is_max_daily(self):
        assert calculate_batch_size(100, 4) == 50
        assert calculate_batch_size(100, 10) == 50

    def test_respects_max_daily_cap(self):
        # Day 3 of 200 contacts = 100, but max_daily=50
        assert calculate_batch_size(200, 3, max_daily=50) == 50

    def test_custom_max_daily(self):
        assert calculate_batch_size(100, 4, max_daily=30) == 30

    def test_small_total_at_least_1(self):
        # 10% of 5 = 0.5 -> int = 0, but should be at least 1
        assert calculate_batch_size(5, 1) == 1

    def test_zero_contacts(self):
        assert calculate_batch_size(0, 1) == 0

    def test_negative_contacts(self):
        assert calculate_batch_size(-10, 1) == 0

    def test_zero_day(self):
        assert calculate_batch_size(100, 0) == 0

    def test_negative_day(self):
        assert calculate_batch_size(100, -1) == 0

    def test_day_4_small_total(self):
        # total_contacts < max_daily
        assert calculate_batch_size(10, 4, max_daily=50) == 10

    def test_large_total(self):
        assert calculate_batch_size(1000, 1) == 50  # 10% = 100, capped at max_daily=50
        assert calculate_batch_size(1000, 2) == 50  # 25% = 250, capped at 50
        assert calculate_batch_size(1000, 3) == 50  # 50% = 500, capped at 50
