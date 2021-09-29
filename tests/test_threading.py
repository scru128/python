from __future__ import annotations

import queue
import threading
import unittest

from scru128 import scru128, Identifier


class TestThreading(unittest.TestCase):
    def test_threading(self) -> None:
        """Generates no IDs sharing same timestamp and counter under multithreading"""

        def producer(q: queue.Queue[str]) -> None:
            for i in range(10000):
                q.put(scru128())

        q: queue.Queue[str] = queue.Queue()
        for i in range(4):
            threading.Thread(target=producer, args=(q,)).start()

        s = set()
        while not (q.empty() and threading.active_count() < 2):
            e = Identifier.from_str(q.get())
            ts_and_cnt = (e.timestamp, e.counter)
            s.add(ts_and_cnt)

        self.assertEqual(len(s), 4 * 10000)
