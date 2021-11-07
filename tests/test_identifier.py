from __future__ import annotations

import copy
import unittest


from scru128 import scru128, Scru128Generator, Scru128Id


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

    def test_symmetric_converters(self) -> None:
        """Has symmetric converters from/to str, int, and fields"""
        g = Scru128Generator()
        for _ in range(1_000):
            obj = g.generate()
            self.assertEqual(Scru128Id.from_str(str(obj)), obj)
            self.assertEqual(Scru128Id(int(obj)), obj)
            self.assertEqual(
                Scru128Id.from_fields(
                    obj.timestamp,
                    obj.counter,
                    obj.per_sec_random,
                    obj.per_gen_random,
                ),
                obj,
            )

    def test_comparison_operators(self) -> None:
        """Supports comparison operators"""
        ordered = [
            Scru128Id.from_fields(0, 0, 0, 0),
            Scru128Id.from_fields(0, 0, 0, 1),
            Scru128Id.from_fields(0, 0, 1, 0),
            Scru128Id.from_fields(0, 1, 0, 0),
            Scru128Id.from_fields(1, 0, 0, 0),
        ]

        g = Scru128Generator()
        for _ in range(1_000):
            ordered.append(g.generate())

        prev = ordered.pop(0)
        for curr in ordered:
            self.assertNotEqual(curr, prev)
            self.assertNotEqual(prev, curr)
            self.assertGreater(curr, prev)
            self.assertGreaterEqual(curr, prev)
            self.assertLess(prev, curr)
            self.assertLessEqual(prev, curr)

            clone = copy.copy(curr)
            self.assertIsNot(curr, clone)
            self.assertIsNot(clone, curr)
            self.assertEqual(curr, clone)
            self.assertEqual(clone, curr)

            prev = curr
