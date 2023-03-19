from __future__ import annotations

import unittest

from scru128 import Scru128Generator, Scru128Id


class TestGenerateCore(unittest.TestCase):
    def test_decreasing_or_constant_timestamp(self) -> None:
        """Generates increasing IDs even with decreasing or constant timestamp"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()
        self.assertEqual(g.last_status, Scru128Generator.Status.NOT_EXECUTED)

        prev = g.generate_core(ts, 10_000)
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)

        for i in range(100_000):
            curr = g.generate_core(ts - min(9_998, i), 10_000)
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

        prev = g.generate_core(ts, 10_000)
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)

        curr = g.generate_core(ts - 10_000, 10_000)
        self.assertEqual(g.last_status, Scru128Generator.Status.CLOCK_ROLLBACK)
        self.assertGreater(prev, curr)
        self.assertEqual(curr.timestamp, ts - 10_000)

        prev = curr
        curr = g.generate_core(ts - 10_001, 10_000)
        self.assertTrue(
            g.last_status == Scru128Generator.Status.COUNTER_LO_INC
            or g.last_status == Scru128Generator.Status.COUNTER_HI_INC
            or g.last_status == Scru128Generator.Status.TIMESTAMP_INC
        )
        self.assertLess(prev, curr)


class TestGenerateCoreNoRewind(unittest.TestCase):
    def test_decreasing_or_constant_timestamp(self) -> None:
        """Generates increasing IDs even with decreasing or constant timestamp"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()
        self.assertEqual(g.last_status, Scru128Generator.Status.NOT_EXECUTED)

        prev = g.generate_core_no_rewind(ts, 10_000)
        assert prev is not None
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)

        for i in range(100_000):
            curr = g.generate_core_no_rewind(ts - min(9_998, i), 10_000)
            assert curr is not None
            self.assertTrue(
                g.last_status == Scru128Generator.Status.COUNTER_LO_INC
                or g.last_status == Scru128Generator.Status.COUNTER_HI_INC
                or g.last_status == Scru128Generator.Status.TIMESTAMP_INC
            )
            self.assertLess(prev, curr)
            prev = curr
        self.assertGreaterEqual(prev.timestamp, ts)

    def test_timestamp_rollback(self) -> None:
        """Returns None if timestamp moves backward a lot"""
        ts = 0x0123_4567_89AB
        g = Scru128Generator()
        self.assertEqual(g.last_status, Scru128Generator.Status.NOT_EXECUTED)

        prev = g.generate_core_no_rewind(ts, 10_000)
        assert prev is not None
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)
        self.assertEqual(prev.timestamp, ts)

        curr = g.generate_core_no_rewind(ts - 10_000, 10_000)
        assert curr is None
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)

        curr = g.generate_core_no_rewind(ts - 10_001, 10_000)
        assert curr is None
        self.assertEqual(g.last_status, Scru128Generator.Status.NEW_TIMESTAMP)


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
