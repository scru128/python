from __future__ import annotations

import unittest

from scru128 import Scru128Generator


class TestGenerator(unittest.TestCase):
    def test_decreasing_or_constant_timestamp(self) -> None:
        """Generates increasing IDs even with decreasing or constant timestamp"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()
        (prev, status) = g.generate_core(ts)
        self.assertEqual(status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)
        for i in range(100_000):
            (curr, status) = g.generate_core(ts - min(9_998, i))
            self.assertTrue(
                status == Scru128Generator.Status.COUNTER_LO_INC
                or status == Scru128Generator.Status.COUNTER_HI_INC
                or status == Scru128Generator.Status.TIMESTAMP_INC
            )
            self.assertLess(prev, curr)
            prev = curr
        self.assertGreaterEqual(prev.timestamp, ts)

    def test_timestamp_rollback(self) -> None:
        """Breaks increasing order of IDs if timestamp moves backward a lot"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()
        (prev, status) = g.generate_core(ts)
        self.assertEqual(status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)
        (curr, status) = g.generate_core(ts - 10_000)
        self.assertEqual(status, Scru128Generator.Status.CLOCK_ROLLBACK)
        self.assertGreater(prev, curr)
        self.assertEqual(curr.timestamp, ts - 10_000)
