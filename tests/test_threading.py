from __future__ import annotations

import queue
import threading
import unittest

from scru128 import scru128, Scru128Id


class TestThreading(unittest.TestCase):
    def test_threading(self) -> None:
        """Generates no IDs sharing same timestamp and counters under multithreading"""

        def producer(q: queue.Queue[Scru128Id]) -> None:
            for i in range(10000):
                q.put(scru128())

        q: queue.Queue[Scru128Id] = queue.Queue()
        for i in range(4):
            threading.Thread(target=producer, args=(q,)).start()

        s = set()
        while not (q.empty() and threading.active_count() < 2):
            e = q.get()
            s.add((e.timestamp, e.counter_hi, e.counter_lo))

        self.assertEqual(len(s), 4 * 10000)
