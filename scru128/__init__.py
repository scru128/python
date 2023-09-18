"""SCRU128: Sortable, Clock and Random number-based Unique identifier"""

from __future__ import annotations

__all__ = [
    "new",
    "new_string",
    "Scru128Generator",
    "Scru128Id",
]

import datetime
import re
import secrets
import threading
import typing


# The maximum value of 48-bit timestamp field.
MAX_TIMESTAMP = 0xFFFF_FFFF_FFFF

# The maximum value of 24-bit counter_hi field.
MAX_COUNTER_HI = 0xFF_FFFF

# The maximum value of 24-bit counter_lo field.
MAX_COUNTER_LO = 0xFF_FFFF

# Digit characters used in the Base36 notation.
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"

# The default timestamp rollback allowance.
DEFAULT_ROLLBACK_ALLOWANCE = 10_000  # 10 seconds


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

    The generator comes with four different methods that generate a SCRU128 ID:

    | Flavor                 | Timestamp | Thread- | On big clock rewind |
    | ---------------------- | --------- | ------- | ------------------- |
    | generate               | Now       | Safe    | Resets generator    |
    | generate_or_abort      | Now       | Safe    | Returns `None`      |
    | generate_or_reset_core | Argument  | Unsafe  | Resets generator    |
    | generate_or_abort_core | Argument  | Unsafe  | Returns `None`      |

    All of the four return a monotonically increasing ID by reusing the previous
    `timestamp` even if the one provided is smaller than the immediately preceding ID's.
    However, when such a clock rollback is considered significant (by default, more than
    ten seconds):

    1.  `generate` (or_reset) methods reset the generator and return a new ID based on
        the given `timestamp`, breaking the increasing order of IDs.
    2.  `or_abort` variants abort and return `None` immediately.

    The `core` functions offer low-level thread-unsafe primitives to customize the
    behavior.
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
        self._lock = threading.Lock()
        if rng is None:
            self._rng = DefaultRandom()
        elif callable(getattr(rng, "getrandbits", None)):
            self._rng = rng
        else:
            raise TypeError("rng does not implement getrandbits()")

    def generate(self) -> Scru128Id:
        """
        Generates a new SCRU128 ID object from the current `timestamp`, or resets the
        generator upon significant timestamp rollback.

        See the Scru128Generator class documentation for the description.
        """
        with self._lock:
            timestamp = datetime.datetime.now().timestamp()
            return self.generate_or_reset_core(
                int(timestamp * 1_000), DEFAULT_ROLLBACK_ALLOWANCE
            )

    def generate_or_abort(self) -> typing.Optional[Scru128Id]:
        """
        Generates a new SCRU128 ID object from the current `timestamp`, or returns
        `None` upon significant timestamp rollback.

        See the Scru128Generator class documentation for the description.
        """
        with self._lock:
            timestamp = datetime.datetime.now().timestamp()
            return self.generate_or_abort_core(
                int(timestamp * 1_000), DEFAULT_ROLLBACK_ALLOWANCE
            )

    def generate_or_reset_core(
        self, timestamp: int, rollback_allowance: int
    ) -> Scru128Id:
        """
        Generates a new SCRU128 ID object from the `timestamp` passed, or resets the
        generator upon significant timestamp rollback.

        See the Scru128Generator class documentation for the description.

        The `rollback_allowance` parameter specifies the amount of `timestamp` rollback
        that is considered significant. A suggested value is `10_000` (milliseconds).

        Unlike `generate()`, this method is NOT thread-safe. The generator object should
        be protected from concurrent accesses using a mutex or other synchronization
        mechanism to avoid race conditions.
        """
        value = self.generate_or_abort_core(timestamp, rollback_allowance)
        if value is None:
            # reset state and resume
            self._timestamp = 0
            self._ts_counter_hi = 0
            value = self.generate_or_abort_core(timestamp, rollback_allowance)
            assert value is not None
        return value

    def generate_or_abort_core(
        self, timestamp: int, rollback_allowance: int
    ) -> typing.Optional[Scru128Id]:
        """
        Generates a new SCRU128 ID object from the `timestamp` passed, or returns `None`
        upon significant timestamp rollback.

        See the Scru128Generator class documentation for the description.

        The `rollback_allowance` parameter specifies the amount of `timestamp` rollback
        that is considered significant. A suggested value is `10_000` (milliseconds).

        Unlike `generate_or_abort()`, this method is NOT thread-safe. The generator
        object should be protected from concurrent accesses using a mutex or other
        synchronization mechanism to avoid race conditions.
        """
        if not (1 <= timestamp <= MAX_TIMESTAMP):
            raise ValueError("`timestamp` must be a 48-bit positive integer")
        elif not (0 <= rollback_allowance <= MAX_TIMESTAMP):
            raise ValueError("`rollback_allowance` out of reasonable range")

        if timestamp > self._timestamp:
            self._timestamp = timestamp
            self._counter_lo = self._rng.getrandbits(24)
        elif timestamp + rollback_allowance >= self._timestamp:
            # go on with previous timestamp if new one is not much smaller
            self._counter_lo += 1
            if self._counter_lo > MAX_COUNTER_LO:
                self._counter_lo = 0
                self._counter_hi += 1
                if self._counter_hi > MAX_COUNTER_HI:
                    self._counter_hi = 0
                    # increment timestamp at counter overflow
                    self._timestamp += 1
                    self._counter_lo = self._rng.getrandbits(24)
        else:
            # abort if clock went backwards to unbearable extent
            return None

        if self._timestamp - self._ts_counter_hi >= 1_000 or self._ts_counter_hi < 1:
            self._ts_counter_hi = self._timestamp
            self._counter_hi = self._rng.getrandbits(24)

        return Scru128Id.from_fields(
            self._timestamp,
            self._counter_hi,
            self._counter_lo,
            self._rng.getrandbits(32),
        )

    def __iter__(self) -> typing.Iterator[Scru128Id]:
        """
        Returns an infinite iterator object that produces a new ID for each call of
        `next()`.
        """
        return self

    def __next__(self) -> Scru128Id:
        """
        Returns a new SCRU128 ID object for each call, infinitely.

        This method is a synonym for `generate()` to use `self` as an infinite iterator.
        """
        return self.generate()


global_generator = Scru128Generator()


def new() -> Scru128Id:
    """
    Generates a new SCRU128 ID object using the global generator.

    This function is thread-safe; multiple threads can call it concurrently.
    """
    return global_generator.generate()


def new_string() -> str:
    """
    Generates a new SCRU128 ID encoded in the 25-digit canonical string representation
    using the global generator.

    This function is thread-safe. Use this to quickly get a new SCRU128 ID as a string.
    """
    return str(new())
