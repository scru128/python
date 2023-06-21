from __future__ import annotations

import unittest

from scru128 import Scru128Generator, Scru128Id


class TestGenerateOrReset(unittest.TestCase):
    def test_decreasing_or_constant_timestamp(self) -> None:
        """Generates increasing IDs even with decreasing or constant timestamp"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()

        prev = g.generate_or_reset_core(ts, 10_000)
        self.assertEqual(prev.timestamp, ts)

        for i in range(100_000):
            curr = g.generate_or_reset_core(ts - min(9_998, i), 10_000)
            self.assertLess(prev, curr)
            prev = curr
        self.assertGreaterEqual(prev.timestamp, ts)

    def test_timestamp_rollback(self) -> None:
        """Breaks increasing order of IDs if timestamp goes backwards a lot"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()

        prev = g.generate_or_reset_core(ts, 10_000)
        self.assertEqual(prev.timestamp, ts)

        curr = g.generate_or_reset_core(ts - 10_000, 10_000)
        self.assertGreater(prev, curr)
        self.assertEqual(curr.timestamp, ts - 10_000)

        prev = curr
        curr = g.generate_or_reset_core(ts - 10_001, 10_000)
        self.assertLess(prev, curr)


class TestGenerateOrAbort(unittest.TestCase):
    def test_decreasing_or_constant_timestamp(self) -> None:
        """Generates increasing IDs even with decreasing or constant timestamp"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()

        prev = g.generate_or_abort_core(ts, 10_000)
        assert prev is not None
        self.assertEqual(prev.timestamp, ts)

        for i in range(100_000):
            curr = g.generate_or_abort_core(ts - min(9_998, i), 10_000)
            assert curr is not None
            self.assertLess(prev, curr)
            prev = curr
        self.assertGreaterEqual(prev.timestamp, ts)

    def test_timestamp_rollback(self) -> None:
        """Returns None if timestamp goes backwards a lot"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()

        prev = g.generate_or_abort_core(ts, 10_000)
        assert prev is not None
        self.assertEqual(prev.timestamp, ts)

        curr = g.generate_or_abort_core(ts - 10_000, 10_000)
        assert curr is None

        curr = g.generate_or_abort_core(ts - 10_001, 10_000)
        assert curr is None


class TestGenerator(unittest.TestCase):
    def test_iterable_implementation(self) -> None:
        """Is iterable with for-in loop"""
        i = 0
        for e in Scru128Generator():
            self.assertIsInstance(e, Scru128Id)
            i += 1
            if i > 100:
                break
        self.assertEqual(i, 101)
