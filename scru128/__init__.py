"""SCRU128: Sortable, Clock and Random number-based Unique identifier"""

from __future__ import annotations

__all__ = ["scru128"]

import datetime
import re
import secrets
import threading
import warnings


# Unix time in milliseconds as at 2020-01-01 00:00:00+00:00.
TIMESTAMP_EPOCH = 1577836800000

# Maximum value of 28-bit counter field.
MAX_COUNTER = 0xFFF_FFFF

# Digit characters used in the base 32 notation.
CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUV"


class Identifier:
    """Represents a SCRU128 ID."""

    __slots__ = "_value"

    def __init__(self, int_value: int) -> None:
        """Creates an object from a 128-bit unsigned integer."""
        self._value = int_value
        if not (0 <= int_value <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF):
            raise ValueError("not a 128-bit unsigned integer")

    @classmethod
    def new(
        cls, timestamp: int, counter: int, per_sec_random: int, per_gen_random: int
    ) -> Identifier:
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
    def from_str(cls, str_value: str) -> Identifier:
        """Creates an object from a 26-digit string representation."""
        if re.match(r"^[0-7][0-9A-V]{25}$", str_value, re.A | re.I) is None:
            raise ValueError(f"invalid string representation: {str_value}")
        return cls(int(str_value, 32))

    def __int__(self) -> int:
        """Returns the 128-bit unsigned integer representation."""
        return self._value

    @property
    def timestamp(self) -> int:
        """44-bit millisecond timestamp field."""
        return (self._value >> 84) & 0xFFF_FFFF_FFFF

    @property
    def counter(self) -> int:
        """28-bit per-millisecond counter field."""
        return (self._value >> 56) & MAX_COUNTER

    @property
    def per_sec_random(self) -> int:
        """24-bit per-second randomness field."""
        return (self._value >> 32) & 0xFF_FFFF

    @property
    def per_gen_random(self) -> int:
        """32-bit per-generation randomness field."""
        return self._value & 0xFFFF_FFFF

    def __str__(self) -> str:
        """Returns the 26-digit canonical string representation."""
        buffer = ["0"] * 26
        n = self._value
        for i in range(26):
            buffer[25 - i] = CHARSET[n & 31]
            n >>= 5
        return "".join(buffer)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(0x{self._value:032X})"


class Generator:
    """Represents a SCRU128 ID generator."""

    def __init__(self) -> None:
        self._ts_last_gen = 0
        self._counter = 0
        self._ts_last_sec = 0
        self._per_sec_random = 0
        self._lock = threading.Lock()

    def generate(self) -> Identifier:
        """Generates a new SCRU128 ID object."""
        with self._lock:
            ts_now = int(datetime.datetime.now().timestamp() * 1000)

            # update timestamp and counter
            if ts_now > self._ts_last_gen:
                self._ts_last_gen = ts_now
                self._counter = secrets.randbits(28)
            else:
                self._counter += 1
                if self._counter > MAX_COUNTER:
                    # wait a moment until clock goes forward when counter overflows
                    n_trials = 0
                    while ts_now <= self._ts_last_gen:
                        ts_now = int(datetime.datetime.now().timestamp() * 1000)
                        n_trials += 1
                        if n_trials > 1_000_000:
                            warnings.warn(
                                "scru128: reset state as clock did not go forward",
                                RuntimeWarning,
                            )
                            self._ts_last_sec = 0
                            break

                    self._ts_last_gen = ts_now
                    self._counter = secrets.randbits(28)

            # update per_sec_random
            if self._ts_last_gen - self._ts_last_sec > 1000:
                self._ts_last_sec = self._ts_last_gen
                self._per_sec_random = secrets.randbits(24)

            return Identifier.new(
                self._ts_last_gen - TIMESTAMP_EPOCH,
                self._counter,
                self._per_sec_random,
                secrets.randbits(32),
            )


default_generator = Generator()


def scru128() -> str:
    """Generates a new SCRU128 ID encoded in a string.

    Returns:
        26-digit canonical string representation.
    """
    return str(default_generator.generate())
