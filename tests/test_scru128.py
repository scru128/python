from __future__ import annotations

import datetime
import unittest

import scru128
from scru128 import Scru128Generator, Scru128Id


class TestScru128(unittest.TestCase):
    def test_type(self) -> None:
        """Returns a Scru128Id object"""
        self.assertIsInstance(scru128.new(), Scru128Id)


class TestScru128String(unittest.TestCase):
    _samples: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls._samples = [scru128.new_string() for _ in range(100_000)]

    def test_format(self) -> None:
        """Generates 25-digit canonical string"""
        for e in self._samples:
            self.assertEqual(type(e), str)
            self.assertRegex(e, r"^[0-9a-z]{25}$")

    def test_uniqueness(self) -> None:
        """Generates 100k identifiers without collision"""
        self.assertEqual(len(set(self._samples)), len(self._samples))

    def test_order(self) -> None:
        """Generates sortable string representation by creation time"""
        for i in range(1, len(self._samples)):
            self.assertLess(self._samples[i - 1], self._samples[i])

    def test_timestamp(self) -> None:
        """Encodes up-to-date timestamp"""
        g = Scru128Generator()
        for i in range(10_000):
            ts_now = int(datetime.datetime.now().timestamp() * 1000)
            timestamp = g.generate().timestamp
            self.assertLess(abs(ts_now - timestamp), 16)

    def test_timestamp_and_counters(self) -> None:
        """Encodes unique sortable tuple of timestamp and counters"""
        prev = Scru128Id.from_str(self._samples[0])
        for e in self._samples[1:]:
            curr = Scru128Id.from_str(e)
            self.assertTrue(
                prev.timestamp < curr.timestamp
                or (
                    prev.timestamp == curr.timestamp
                    and prev.counter_hi < curr.counter_hi
                )
                or (
                    prev.timestamp == curr.timestamp
                    and prev.counter_hi == curr.counter_hi
                    and prev.counter_lo < curr.counter_lo
                )
            )
            prev = curr
