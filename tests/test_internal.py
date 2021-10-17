from __future__ import annotations

import unittest

from scru128 import scru128, Scru128Id


class TestIdentifier(unittest.TestCase):
    def test_encode_decode(self) -> None:
        """Encodes and decodes prepared cases correctly"""
        cases = [
            ((0, 0, 0, 0), "00000000000000000000000000"),
            ((2 ** 44 - 1, 0, 0, 0), "7VVVVVVVVG0000000000000000"),
            ((0, 2 ** 28 - 1, 0, 0), "000000000FVVVVU00000000000"),
            ((0, 0, 2 ** 24 - 1, 0), "000000000000001VVVVS000000"),
            ((0, 0, 0, 2 ** 32 - 1), "00000000000000000003VVVVVV"),
            (
                (2 ** 44 - 1, 2 ** 28 - 1, 2 ** 24 - 1, 2 ** 32 - 1),
                "7VVVVVVVVVVVVVVVVVVVVVVVVV",
            ),
        ]

        for e in cases:
            from_fields = Scru128Id.from_fields(*e[0])
            from_str = Scru128Id.from_str(e[1])
            self.assertEqual(int(from_fields), int(e[1], 32))
            self.assertEqual(int(from_str), int(e[1], 32))
            self.assertEqual(
                (
                    (
                        from_fields.timestamp,
                        from_fields.counter,
                        from_fields.per_sec_random,
                        from_fields.per_gen_random,
                    ),
                    str(from_fields),
                ),
                e,
            )
            self.assertEqual(
                (
                    (
                        from_str.timestamp,
                        from_str.counter,
                        from_str.per_sec_random,
                        from_str.per_gen_random,
                    ),
                    str(from_str),
                ),
                e,
            )

    def test_symmetry(self) -> None:
        """Has symmetric from_str() and __str__()"""
        for _ in range(1_000):
            src = scru128()
            self.assertEqual(str(Scru128Id.from_str(src)), src)
