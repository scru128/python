"""SCRU128: Sortable, Clock and Random number-based Unique identifier"""

from __future__ import annotations

__all__ = [
    "scru128",
    "scru128_string",
    "Scru128Generator",
    "Scru128Id",
]

import datetime
import enum
import re
import secrets
import threading
import typing


# Maximum value of 48-bit timestamp field.
MAX_TIMESTAMP = 0xFFFF_FFFF_FFFF

# Maximum value of 24-bit counter_hi field.
MAX_COUNTER_HI = 0xFF_FFFF

# Maximum value of 24-bit counter_lo field.
MAX_COUNTER_LO = 0xFF_FFFF

# Digit characters used in the Base36 notation.
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Scru128Id:
    """
    Represents a SCRU128 ID and provides converters and comparison operators.
    """

    __slots__ = "_value"

    def __init__(self, int_value: int) -> None:
        """Creates an object from a 128-bit unsigned integer."""
        self._value = int_value
        if not (0 <= int_value <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF):
            raise ValueError("not a 128-bit unsigned integer")

    @classmethod
    def from_fields(
        cls, timestamp: int, counter_hi: int, counter_lo: int, entropy: int
    ) -> Scru128Id:
        """Creates an object from field values."""
        if not (
            0 <= timestamp <= MAX_TIMESTAMP
            and 0 <= counter_hi <= MAX_COUNTER_HI
            and 0 <= counter_lo <= MAX_COUNTER_LO
            and 0 <= entropy <= 0xFFFF_FFFF
        ):
            raise ValueError("invalid field value")
        return cls(
            (timestamp << 80) | (counter_hi << 56) | (counter_lo << 32) | entropy
        )

    @classmethod
    def from_str(cls, str_value: str) -> Scru128Id:
        """Creates an object from a 25-digit string representation."""
        if re.match(r"^[0-9A-Za-z]{25}$", str_value) is None:
            raise ValueError("invalid string representation")
        return cls(int(str_value, 36))

    def __int__(self) -> int:
        """Returns the 128-bit unsigned integer representation."""
        return self._value

    @property
    def timestamp(self) -> int:
        """Returns the 48-bit timestamp field value."""
        return (self._value >> 80) & MAX_TIMESTAMP

    @property
    def counter_hi(self) -> int:
        """Returns the 24-bit counter_hi field value."""
        return (self._value >> 56) & MAX_COUNTER_HI

    @property
    def counter_lo(self) -> int:
        """Returns the 24-bit counter_lo field value."""
        return (self._value >> 32) & MAX_COUNTER_LO

    @property
    def entropy(self) -> int:
        """Returns the 32-bit entropy field value."""
        return self._value & 0xFFFF_FFFF

    def __str__(self) -> str:
        """Returns the 25-digit canonical string representation."""
        buffer = ["0"] * 25
        n = self._value
        for i in range(25):
            (n, rem) = divmod(n, 36)
            buffer[24 - i] = DIGITS[rem]
        return "".join(buffer)

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
    Represents a SCRU128 ID generator that encapsulates the monotonic counters and other
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
        self._timestamp = 0
        self._counter_hi = 0
        self._counter_lo = 0
        self._ts_counter_hi = 0
        self._last_status = Scru128Generator.Status.NOT_EXECUTED
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

        This method is thread-safe; multiple threads can call it concurrently.
        """
        with self._lock:
            timestamp = datetime.datetime.now().timestamp()
            return self.generate_core(int(timestamp * 1_000))

    def generate_core(self, timestamp: int) -> Scru128Id:
        """
        Generates a new SCRU128 ID object with the timestamp passed.

        Unlike `generate()`, this method is NOT thread-safe. The generator object should
        be protected from concurrent accesses using a mutex or other synchronization
        mechanism to avoid race conditions.
        """
        if not (0 <= timestamp <= MAX_TIMESTAMP):
            raise ValueError("`timestamp` must be a 48-bit unsigned integer")

        self._last_status = Scru128Generator.Status.NEW_TIMESTAMP
        if timestamp > self._timestamp:
            self._timestamp = timestamp
            self._counter_lo = self._rng.getrandbits(24)
        elif timestamp + 10_000 > self._timestamp:
            self._counter_lo += 1
            self._last_status = Scru128Generator.Status.COUNTER_LO_INC
            if self._counter_lo > MAX_COUNTER_LO:
                self._counter_lo = 0
                self._counter_hi += 1
                self._last_status = Scru128Generator.Status.COUNTER_HI_INC
                if self._counter_hi > MAX_COUNTER_HI:
                    self._counter_hi = 0
                    # increment timestamp at counter overflow
                    self._timestamp += 1
                    self._counter_lo = self._rng.getrandbits(24)
                    self._last_status = Scru128Generator.Status.TIMESTAMP_INC
        else:
            # reset state if clock moves back by ten seconds or more
            self._ts_counter_hi = 0
            self._timestamp = timestamp
            self._counter_lo = self._rng.getrandbits(24)
            self._last_status = Scru128Generator.Status.CLOCK_ROLLBACK

        if self._timestamp - self._ts_counter_hi >= 1_000:
            self._ts_counter_hi = self._timestamp
            self._counter_hi = self._rng.getrandbits(24)

        return Scru128Id.from_fields(
            self._timestamp,
            self._counter_hi,
            self._counter_lo,
            self._rng.getrandbits(32),
        )

    @property
    def last_status(self) -> Scru128Generator.Status:
        """
        Returns a `Status` code that indicates the internal state involved in the last
        generation of ID.

        Note that the generator object should be protected from concurrent accesses
        during the sequential calls to a generation method and this property to avoid
        race conditions.
        """
        return self._last_status

    class Status(enum.Enum):
        """
        Status code returned by `last_status` property.

        Attributes:
            NOT_EXECUTED: Indicates that the generator has yet to generate an ID.
            NEW_TIMESTAMP: Indicates that the latest timestamp was used because it was
                greater than the previous one.
            COUNTER_LO_INC: Indicates that counter_lo was incremented because the latest
                timestamp was no greater than the previous one.
            COUNTER_HI_INC: Indicates that counter_hi was incremented because counter_lo
                reached its maximum value.
            TIMESTAMP_INC: Indicates that the previous timestamp was incremented because
                counter_hi reached its maximum value.
            CLOCK_ROLLBACK: Indicates that the monotonic order of generated IDs was
                broken because the latest timestamp was less than the previous one by
                ten seconds or more.
        """

        NOT_EXECUTED = enum.auto()
        NEW_TIMESTAMP = enum.auto()
        COUNTER_LO_INC = enum.auto()
        COUNTER_HI_INC = enum.auto()
        TIMESTAMP_INC = enum.auto()
        CLOCK_ROLLBACK = enum.auto()


default_generator = Scru128Generator()


def scru128() -> Scru128Id:
    """
    Generates a new SCRU128 ID object.

    This function is thread-safe; multiple threads can call it concurrently.
    """
    return default_generator.generate()


def scru128_string() -> str:
    """
    Generates a new SCRU128 ID encoded in the 25-digit canonical string representation.

    This function is thread-safe. Use this to quickly get a new SCRU128 ID as a string.
    """
    return str(scru128())
