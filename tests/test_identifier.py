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
                (e[0], e[1].lower()),
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
                (e[0], e[1].lower()),
            )

    def test_string_validation(self) -> None:
        """Raises error if an invalid string representation is supplied"""
        cases = [
            "",
            " 036z8puq4tsxsigk6o19y164q",
            "036z8puq54qny1vq3hcbrkweb ",
            " 036z8puq54qny1vq3helivwax ",
            "+036z8puq54qny1vq3hfcv3ss0",
            "-036z8puq54qny1vq3hhy8u1ch",
            "+36z8puq54qny1vq3hjq48d9p",
            "-36z8puq5a7j0ti08oz6zdrdy",
            "036z8puq5a7j0t_08p2cdz28v",
            "036z8pu-5a7j0ti08p3ol8ool",
            "036z8puq5a7j0ti08p4j 6cya",
            "f5lxx1zz5pnorynqglhzmsp34",
            "zzzzzzzzzzzzzzzzzzzzzzzzz",
            "039o\tvvklfmqlqe7fzllz7c7t",
            "039onvvklfmqlq漢字fgvd1",
            "039onvvkl🤣qe7fzr2hdoqu",
            "頭onvvklfmqlqe7fzrhtgcfz",
            "039onvvklfmqlqe7fztft5尾",
            "039漢字a52xp4bvf4sn94e09cja",
            "039ooa52xp4bv😘sn97642mwl",
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
