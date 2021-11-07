from __future__ import annotations

import datetime
import unittest

from scru128 import scru128, Scru128Generator, Scru128Id


class TestScru128(unittest.TestCase):
    _samples: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls._samples = [scru128() for _ in range(100_000)]

    def test_format(self) -> None:
        """Generates 26-digit canonical string"""
        for e in self._samples:
            self.assertEqual(type(e), str)
            self.assertRegex(e, r"^[0-7][0-9A-V]{25}$")

    def test_uniqueness(self) -> None:
        """Generates 100k identifiers without collision"""
        self.assertEqual(len(set(self._samples)), len(self._samples))

    def test_order(self) -> None:
        """Generates sortable string representation by creation time"""
        for i in range(1, len(self._samples)):
            self.assertLess(self._samples[i - 1], self._samples[i])

    def test_timestamp(self) -> None:
        """Encodes up-to-date timestamp"""
        epoch = int(
            datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp()
            * 1000
        )
        g = Scru128Generator()
        for i in range(10_000):
            ts_now = int(datetime.datetime.now().timestamp() * 1000) - epoch
            timestamp = g.generate().timestamp
            self.assertLess(abs(ts_now - timestamp), 16)

    def test_timestamp_and_counter(self) -> None:
        """Encodes unique sortable pair of timestamp and counter"""
        prev = Scru128Id.from_str(self._samples[0])
        for e in self._samples[1:]:
            curr = Scru128Id.from_str(e)
            self.assertTrue(
                prev.timestamp < curr.timestamp
                or (prev.timestamp == curr.timestamp and prev.counter < curr.counter)
            )
            prev = curr
