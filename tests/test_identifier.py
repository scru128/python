from __future__ import annotations

import copy
import unittest

from scru128 import Scru128Generator, Scru128Id

MAX_UINT48 = 2**48 - 1
MAX_UINT24 = 2**24 - 1
MAX_UINT32 = 2**32 - 1


class TestIdentifier(unittest.TestCase):
    def test_encode_decode(self) -> None:
        """Encodes and decodes prepared cases correctly"""
        cases = [
            ((0, 0, 0, 0), "0000000000000000000000000"),
            ((MAX_UINT48, 0, 0, 0), "F5LXX1ZZ5K6TP71GEEH2DB7K0"),
            ((MAX_UINT48, 0, 0, 0), "f5lxx1zz5k6tp71geeh2db7k0"),
            ((0, MAX_UINT24, 0, 0), "0000000005GV2R2KJWR7N8XS0"),
            ((0, MAX_UINT24, 0, 0), "0000000005gv2r2kjwr7n8xs0"),
            ((0, 0, MAX_UINT24, 0), "00000000000000JPIA7QL4HS0"),
            ((0, 0, MAX_UINT24, 0), "00000000000000jpia7ql4hs0"),
            ((0, 0, 0, MAX_UINT32), "0000000000000000001Z141Z3"),
            ((0, 0, 0, MAX_UINT32), "0000000000000000001z141z3"),
            (
                (MAX_UINT48, MAX_UINT24, MAX_UINT24, MAX_UINT32),
                "F5LXX1ZZ5PNORYNQGLHZMSP33",
            ),
            (
                (MAX_UINT48, MAX_UINT24, MAX_UINT24, MAX_UINT32),
                "f5lxx1zz5pnorynqglhzmsp33",
            ),
        ]

        for e in cases:
            from_fields = Scru128Id.from_fields(*e[0])
            from_string = Scru128Id.from_str(e[1])
            self.assertEqual(int(from_fields), int(e[1], 36))
            self.assertEqual(int(from_string), int(e[1], 36))
            self.assertEqual(
                (
                    (
                        from_fields.timestamp,
                        from_fields.counter_hi,
                        from_fields.counter_lo,
                        from_fields.entropy,
                    ),
                    str(from_fields),
                ),
                (e[0], e[1].upper()),
            )
            self.assertEqual(
                (
                    (
                        from_string.timestamp,
                        from_string.counter_hi,
                        from_string.counter_lo,
                        from_string.entropy,
                    ),
                    str(from_string),
                ),
                (e[0], e[1].upper()),
            )

    def test_string_validation(self) -> None:
        """Raises error if an invalid string representation is supplied"""
        cases = [
            "",
            " 036Z8PUQ4TSXSIGK6O19Y164Q",
            "036Z8PUQ54QNY1VQ3HCBRKWEB ",
            " 036Z8PUQ54QNY1VQ3HELIVWAX ",
            "+036Z8PUQ54QNY1VQ3HFCV3SS0",
            "-036Z8PUQ54QNY1VQ3HHY8U1CH",
            "+36Z8PUQ54QNY1VQ3HJQ48D9P",
            "-36Z8PUQ5A7J0TI08OZ6ZDRDY",
            "036Z8PUQ5A7J0T_08P2CDZ28V",
            "036Z8PU-5A7J0TI08P3OL8OOL",
            "036Z8PUQ5A7J0TI08P4J 6CYA",
            "F5LXX1ZZ5PNORYNQGLHZMSP34",
            "ZZZZZZZZZZZZZZZZZZZZZZZZZ",
            "039O\tVVKLFMQLQE7FZLLZ7C7T",
            "039ONVVKLFMQLQ漢字FGVD1",
            "039ONVVKL🤣QE7FZR2HDOQU",
            "頭ONVVKLFMQLQE7FZRHTGCFZ",
            "039ONVVKLFMQLQE7FZTFT5尾",
            "039漢字A52XP4BVF4SN94E09CJA",
            "039OOA52XP4BV😘SN97642MWL",
        ]

        for e in cases:
            with self.assertRaises(ValueError):
                Scru128Id.from_str(e)

    def test_symmetric_converters(self) -> None:
        """Has symmetric converters from/to various values"""
        cases = [
            Scru128Id.from_fields(0, 0, 0, 0),
            Scru128Id.from_fields(MAX_UINT48, 0, 0, 0),
            Scru128Id.from_fields(0, MAX_UINT24, 0, 0),
            Scru128Id.from_fields(0, 0, MAX_UINT24, 0),
            Scru128Id.from_fields(0, 0, 0, MAX_UINT32),
            Scru128Id.from_fields(MAX_UINT48, MAX_UINT24, MAX_UINT24, MAX_UINT32),
        ]

        g = Scru128Generator()
        for _ in range(1_000):
            cases.append(g.generate())

        for e in cases:
            self.assertEqual(Scru128Id.from_str(str(e)), e)
            self.assertEqual(Scru128Id(int(e)), e)
            self.assertEqual(
                Scru128Id.from_fields(
                    e.timestamp, e.counter_hi, e.counter_lo, e.entropy
                ),
                e,
            )

    def test_comparison_operators(self) -> None:
        """Supports comparison operators"""
        ordered = [
            Scru128Id.from_fields(0, 0, 0, 0),
            Scru128Id.from_fields(0, 0, 0, 1),
            Scru128Id.from_fields(0, 0, 0, MAX_UINT32),
            Scru128Id.from_fields(0, 0, 1, 0),
            Scru128Id.from_fields(0, 0, MAX_UINT24, 0),
            Scru128Id.from_fields(0, 1, 0, 0),
            Scru128Id.from_fields(0, MAX_UINT24, 0, 0),
            Scru128Id.from_fields(1, 0, 0, 0),
            Scru128Id.from_fields(2, 0, 0, 0),
        ]

        g = Scru128Generator()
        for _ in range(1_000):
            ordered.append(g.generate())

        prev = ordered.pop(0)
        for curr in ordered:
            self.assertNotEqual(curr, prev)
            self.assertNotEqual(prev, curr)
            self.assertNotEqual(hash(curr), hash(prev))
            self.assertGreater(curr, prev)
            self.assertGreaterEqual(curr, prev)
            self.assertLess(prev, curr)
            self.assertLessEqual(prev, curr)

            clone = copy.copy(curr)
            self.assertIsNot(curr, clone)
            self.assertIsNot(clone, curr)
            self.assertEqual(curr, clone)
            self.assertEqual(clone, curr)
            self.assertEqual(hash(curr), hash(clone))
            self.assertGreaterEqual(curr, clone)
            self.assertGreaterEqual(clone, curr)
            self.assertLessEqual(curr, clone)
            self.assertLessEqual(clone, curr)

            prev = curr
