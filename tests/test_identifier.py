from __future__ import annotations

import copy
import unittest


from scru128 import Scru128Generator, Scru128Id

MAX_UINT44 = 2 ** 44 - 1
MAX_UINT28 = 2 ** 28 - 1
MAX_UINT24 = 2 ** 24 - 1
MAX_UINT32 = 2 ** 32 - 1


class TestIdentifier(unittest.TestCase):
    def test_encode_decode(self) -> None:
        """Encodes and decodes prepared cases correctly"""
        cases = [
            ((0, 0, 0, 0), "00000000000000000000000000"),
            ((MAX_UINT44, 0, 0, 0), "7VVVVVVVVG0000000000000000"),
            ((MAX_UINT44, 0, 0, 0), "7vvvvvvvvg0000000000000000"),
            ((0, MAX_UINT28, 0, 0), "000000000FVVVVU00000000000"),
            ((0, MAX_UINT28, 0, 0), "000000000fvvvvu00000000000"),
            ((0, 0, MAX_UINT24, 0), "000000000000001VVVVS000000"),
            ((0, 0, MAX_UINT24, 0), "000000000000001vvvvs000000"),
            ((0, 0, 0, MAX_UINT32), "00000000000000000003VVVVVV"),
            ((0, 0, 0, MAX_UINT32), "00000000000000000003vvvvvv"),
            (
                (MAX_UINT44, MAX_UINT28, MAX_UINT24, MAX_UINT32),
                "7VVVVVVVVVVVVVVVVVVVVVVVVV",
            ),
            (
                (MAX_UINT44, MAX_UINT28, MAX_UINT24, MAX_UINT32),
                "7vvvvvvvvvvvvvvvvvvvvvvvvv",
            ),
        ]

        for e in cases:
            from_fields = Scru128Id.from_fields(*e[0])
            from_string = Scru128Id.from_str(e[1])
            self.assertEqual(int(from_fields), int(e[1], 32))
            self.assertEqual(int(from_string), int(e[1], 32))
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
                (e[0], e[1].upper()),
            )
            self.assertEqual(
                (
                    (
                        from_string.timestamp,
                        from_string.counter,
                        from_string.per_sec_random,
                        from_string.per_gen_random,
                    ),
                    str(from_string),
                ),
                (e[0], e[1].upper()),
            )

    def test_string_validation(self) -> None:
        """Raises error if an invalid string representation is supplied"""
        cases = [
            "",
            " 00SCT4FL89GQPRHN44C4LFM0OV",
            "00SCT4FL89GQPRJN44C7SQO381 ",
            " 00SCT4FL89GQPRLN44C4BGCIIO ",
            "+00SCT4FL89GQPRNN44C4F3QD24",
            "-00SCT4FL89GQPRPN44C7H4E5RC",
            "+0SCT4FL89GQPRRN44C55Q7RVC",
            "-0SCT4FL89GQPRTN44C6PN0A2R",
            "00SCT4FL89WQPRVN44C41RGVMM",
            "00SCT4FL89GQPS1N4_C54QDC5O",
            "00SCT4-L89GQPS3N44C602O0K8",
            "00SCT4FL89GQPS N44C7VHS5QJ",
            "80000000000000000000000000",
            "VVVVVVVVVVVVVVVVVVVVVVVVVV",
        ]

        for e in cases:
            with self.assertRaises(ValueError):
                Scru128Id.from_str(e)

    def test_symmetric_converters(self) -> None:
        """Has symmetric converters from/to various values"""
        cases = [
            Scru128Id.from_fields(0, 0, 0, 0),
            Scru128Id.from_fields(MAX_UINT44, 0, 0, 0),
            Scru128Id.from_fields(0, MAX_UINT28, 0, 0),
            Scru128Id.from_fields(0, 0, MAX_UINT24, 0),
            Scru128Id.from_fields(0, 0, 0, MAX_UINT32),
            Scru128Id.from_fields(MAX_UINT44, MAX_UINT28, MAX_UINT24, MAX_UINT32),
        ]

        g = Scru128Generator()
        for _ in range(1_000):
            cases.append(g.generate())

        for e in cases:
            self.assertEqual(Scru128Id.from_str(str(e)), e)
            self.assertEqual(Scru128Id(int(e)), e)
            self.assertEqual(
                Scru128Id.from_fields(
                    e.timestamp, e.counter, e.per_sec_random, e.per_gen_random
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
            Scru128Id.from_fields(0, MAX_UINT28, 0, 0),
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
