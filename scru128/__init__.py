"""SCRU128: Sortable, Clock and Random number-based Unique identifier"""

from __future__ import annotations

__all__ = [
    "scru128",
    "scru128_string",
    "Scru128Generator",
    "Scru128Id",
    "TIMESTAMP_BIAS",
]

import datetime
import logging
import re
import secrets
import threading
import typing

# Unix time in milliseconds at 2020-01-01 00:00:00+00:00.
TIMESTAMP_BIAS = 1577836800000

# Maximum value of 28-bit counter field.
MAX_COUNTER = 0xFFF_FFFF

# Digit characters used in the base 32 notation.
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUV"


class Scru128Id:
    """
    Represents a SCRU128 ID and provides various converters and comparison operators.
    """

    __slots__ = "_value"

    def __init__(self, int_value: int) -> None:
        """Creates an object from a 128-bit unsigned integer."""
        self._value = int_value
        if not (0 <= int_value <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF):
            raise ValueError("not a 128-bit unsigned integer")

    @classmethod
    def from_fields(
        cls, timestamp: int, counter: int, per_sec_random: int, per_gen_random: int
    ) -> Scru128Id:
        """Creates an object from field values."""
        if not (
            0 <= timestamp <= 0xFFF_FFFF_FFFF
            and 0 <= counter <= MAX_COUNTER
            and 0 <= per_sec_random <= 0xFF_FFFF
            and 0 <= per_gen_random <= 0xFFFF_FFFF
        ):
            raise ValueError("invalid field value")
        return cls(
            (timestamp << 84)
            | (counter << 56)
            | (per_sec_random << 32)
            | per_gen_random
        )

    @classmethod
    def from_str(cls, str_value: str) -> Scru128Id:
        """Creates an object from a 26-digit string representation."""
        if re.match(r"^[0-7][0-9A-Va-v]{25}$", str_value) is None:
            raise ValueError("invalid string representation")
        return cls(int(str_value, 32))

    def __int__(self) -> int:
        """Returns the 128-bit unsigned integer representation."""
        return self._value

    @property
    def timestamp(self) -> int:
        """Returns the 44-bit millisecond timestamp field value."""
        return (self._value >> 84) & 0xFFF_FFFF_FFFF

    @property
    def counter(self) -> int:
        """Returns the 28-bit per-timestamp monotonic counter field value."""
        return (self._value >> 56) & MAX_COUNTER

    @property
    def per_sec_random(self) -> int:
        """Returns the 24-bit per-second randomness field value."""
        return (self._value >> 32) & 0xFF_FFFF

    @property
    def per_gen_random(self) -> int:
        """Returns the 32-bit per-generation randomness field value."""
        return self._value & 0xFFFF_FFFF

    def __str__(self) -> str:
        """Returns the 26-digit canonical string representation."""
        cache = self._value
        return "".join([DIGITS[(cache >> i) & 31] for i in range(125, -1, -5)])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(0x{self._value:032X})"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented
        return self._value == value._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __lt__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented
        return self._value < value._value

    def __le__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented
        return self._value <= value._value

    def __gt__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented
        return self._value > value._value

    def __ge__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented
        return self._value >= value._value


class DefaultRandom:
    def getrandbits(self, k: int) -> int:
        return secrets.randbits(k)


class Scru128Generator:
    """
    Represents a SCRU128 ID generator that encapsulates the monotonic counter and other
    internal states.
    """

    def __init__(self, *, rng: typing.Any = None) -> None:
        """
        Creates a generator object with the default random number generator, or with the
        specified one if passed as an argument. The specified random number generator
        should be cryptographically strong and securely seeded.

        Args:
            rng: Any object that implements a k-bit random unsigned integer generation
                 method: `getrandbits(k: int) -> int`. The interface is compatible with
                 random.Random and random.SystemRandom.
        """
        self._ts_last_gen = 0
        self._counter = 0
        self._ts_last_sec = 0
        self._per_sec_random = 0
        self._n_clock_check_max = 1_000_000
        self._lock = threading.Lock()
        if rng is None:
            self._rng = DefaultRandom()
        elif callable(getattr(rng, "getrandbits", None)):
            self._rng = rng
        else:
            raise TypeError("rng does not implement getrandbits()")

    def generate(self) -> Scru128Id:
        """
        Generates a new SCRU128 ID object.

        This method is thread safe; multiple threads can call it concurrently.
        """
        with self._lock:
            return self._generate_thread_unsafe()

    def _generate_thread_unsafe(self) -> Scru128Id:
        """Generates a new SCRU128 ID object without overhead for thread safety."""
        # update timestamp and counter
        ts_now = int(datetime.datetime.now().timestamp() * 1000)
        if ts_now > self._ts_last_gen:
            self._ts_last_gen = ts_now
            self._counter = self._rng.getrandbits(28)
        else:
            self._counter += 1
            if self._counter > MAX_COUNTER:
                logger = logging.getLogger("scru128")
                logger.info("counter limit reached; will wait until clock goes forward")
                n_clock_check = 0
                while ts_now <= self._ts_last_gen:
                    ts_now = int(datetime.datetime.now().timestamp() * 1000)
                    n_clock_check += 1
                    if n_clock_check > self._n_clock_check_max:
                        logger.warning("reset state as clock did not go forward")
                        self._ts_last_sec = 0
                        break

                self._ts_last_gen = ts_now
                self._counter = self._rng.getrandbits(28)

        # update per_sec_random
        if self._ts_last_gen - self._ts_last_sec > 1000:
            self._ts_last_sec = self._ts_last_gen
            self._per_sec_random = self._rng.getrandbits(24)

        return Scru128Id.from_fields(
            self._ts_last_gen - TIMESTAMP_BIAS,
            self._counter,
            self._per_sec_random,
            self._rng.getrandbits(32),
        )


default_generator = Scru128Generator()


def scru128() -> Scru128Id:
    """
    Generates a new SCRU128 ID object.

    This function is thread safe; multiple threads can call it concurrently.
    """
    return default_generator.generate()


def scru128_string() -> str:
    """
    Generates a new SCRU128 ID encoded in the 26-digit canonical string representation.

    This function is thread safe. Use this to quickly get a new SCRU128 ID as a string.
    """
    return str(scru128())
