from __future__ import annotations

import unittest

from scru128 import Scru128Generator


class TestGenerator(unittest.TestCase):
    def test_decreasing_or_constant_timestamp(self) -> None:
        """Generates increasing IDs even with decreasing or constant timestamp"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()
        self.assertEqual(g.last_status, Scru128Generator.Status.NOT_EXECUTED)

        prev = g.generate_core(ts)
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)

        for i in range(100_000):
            curr = g.generate_core(ts - min(9_998, i))
            self.assertTrue(
                g.last_status == Scru128Generator.Status.COUNTER_LO_INC
                or g.last_status == Scru128Generator.Status.COUNTER_HI_INC
                or g.last_status == Scru128Generator.Status.TIMESTAMP_INC
            )
            self.assertLess(prev, curr)
            prev = curr
        self.assertGreaterEqual(prev.timestamp, ts)

    def test_timestamp_rollback(self) -> None:
        """Breaks increasing order of IDs if timestamp moves backward a lot"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()
        self.assertEqual(g.last_status, Scru128Generator.Status.NOT_EXECUTED)

        prev = g.generate_core(ts)
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)

        curr = g.generate_core(ts - 10_000)
        self.assertEqual(g.last_status, Scru128Generator.Status.CLOCK_ROLLBACK)
        self.assertGreater(prev, curr)
        self.assertEqual(curr.timestamp, ts - 10_000)
