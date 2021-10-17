from __future__ import annotations

import queue
import threading
import unittest

from scru128 import scru128, Scru128Id


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
            e = Scru128Id.from_str(q.get())
            s.add((e.timestamp, e.counter))

        self.assertEqual(len(s), 4 * 10000)
