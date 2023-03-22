"""SCRU128: Sortable, Clock and Random number-based Unique identifier"""

from __future__ import annotations

__all__ = [
    "new",
    "new_string",
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
import warnings


# The maximum value of 48-bit timestamp field.
MAX_TIMESTAMP = 0xFFFF_FFFF_FFFF

# The maximum value of 24-bit counter_hi field.
MAX_COUNTER_HI = 0xFF_FFFF

# The maximum value of 24-bit counter_lo field.
MAX_COUNTER_LO = 0xFF_FFFF

# Digit characters used in the Base36 notation.
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

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

    The generator offers four different methods to generate a SCRU128 ID:

    | Flavor                 | Timestamp | Thread- | On big clock rewind |
    | ---------------------- | --------- | ------- | ------------------- |
    | generate               | Now       | Safe    | Resets generator    |
    | generate_or_abort      | Now       | Safe    | Returns `None`      |
    | generate_or_reset_core | Argument  | Unsafe  | Resets generator    |
    | generate_or_abort_core | Argument  | Unsafe  | Returns `None`      |

    All of these methods return monotonically increasing IDs unless a `timestamp`
    provided is significantly (by default, ten seconds or more) smaller than the one
    embedded in the immediately preceding ID. If such a significant clock rollback is
    detected, the `generate` (or_reset) method resets the generator and returns a new ID
    based on the given `timestamp`, while the `or_abort` variants abort and return
    `None`. The `core` functions offer low-level thread-unsafe primitives.
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
            self._last_status = Scru128Generator.Status.CLOCK_ROLLBACK
            assert value is not None
        return value

    def generate_core(self, timestamp: int) -> Scru128Id:
        """
        Deprecated: Use `generate_or_reset_core(timestamp, 10_000)` instead.

        A deprecated synonym for `generate_or_reset_core(timestamp, 10_000)`.
        """
        warnings.warn(
            "use `generate_or_reset_core(timestamp, 10_000)` instead",
            DeprecationWarning,
        )
        return self.generate_or_reset_core(timestamp, DEFAULT_ROLLBACK_ALLOWANCE)

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
            self._last_status = Scru128Generator.Status.NEW_TIMESTAMP
        elif timestamp + rollback_allowance > self._timestamp:
            # go on with previous timestamp if new one is not much smaller
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

    @property
    def last_status(self) -> Scru128Generator.Status:
        """
        Deprecated: Use `generate_or_abort()` to guarantee monotonicity.

        Returns a `Status` code that indicates the internal state involved in the last
        generation of ID.

        Note that the generator object should be protected from concurrent accesses
        during the sequential calls to a generation method and this property to avoid
        race conditions.
        """
        warnings.warn(
            "use `generate_or_abort()` to guarantee monotonicity",
            DeprecationWarning,
        )
        return self._last_status

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

    class Status(enum.Enum):
        """
        Deprecated: Use `generate_or_abort()` to guarantee monotonicity.

        The status code returned by `last_status` property.

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


def scru128() -> Scru128Id:
    """A deprecated synonym for `new()` (deprecated since v2.2.0)."""
    warnings.warn("use `scru128.new()` (synonym)", DeprecationWarning)
    return new()


def scru128_string() -> str:
    """A deprecated synonym for `new_string()` (deprecated since v2.2.0)."""
    warnings.warn("use `scru128.new_string()` (synonym)", DeprecationWarning)
    return new_string()
