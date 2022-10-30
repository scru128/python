# SCRU128: Sortable, Clock and Random number-based Unique identifier

[![PyPI](https://img.shields.io/pypi/v/scru128)](https://pypi.org/project/scru128/)
[![License](https://img.shields.io/pypi/l/scru128)](https://github.com/scru128/python/blob/main/LICENSE)

SCRU128 ID is yet another attempt to supersede [UUID] for the users who need
decentralized, globally unique time-ordered identifiers. SCRU128 is inspired by
[ULID] and [KSUID] and has the following features:

- 128-bit unsigned integer type
- Sortable by generation time (as integer and as text)
- 25-digit case-insensitive textual representation (Base36)
- 48-bit millisecond Unix timestamp that ensures useful life until year 10889
- Up to 281 trillion time-ordered but unpredictable unique IDs per millisecond
- 80-bit three-layer randomness for global uniqueness

```python
import scru128

# generate a new identifier object
x = scru128.new()
print(x)  # e.g. "036Z951MHJIKZIK2GSL81GR7L"
print(int(x))  # as a 128-bit unsigned integer

# generate a textual representation directly
print(scru128.new_string())  # e.g. "036Z951MHZX67T63MQ9XE6Q0J"
```

See [SCRU128 Specification] for details.

[uuid]: https://en.wikipedia.org/wiki/Universally_unique_identifier
[ulid]: https://github.com/ulid/spec
[ksuid]: https://github.com/segmentio/ksuid
[scru128 specification]: https://github.com/scru128/spec

## Command-line interface

`scru128` generates SCRU128 IDs.

```bash
$ scru128
036ZG4ZLMDWDZ8414EIM77VCT
$ scru128 -n 4
036ZG4ZLV707WNCZL108KY4I7
036ZG4ZLV707WNCZL12TOWMHO
036ZG4ZLV707WNCZL14HIRM6N
036ZG4ZLV707WNCZL17110SHH
```

`scru128-inspect` prints the components of given SCRU128 IDs as human- and
machine-readable JSON objects.

```bash
$ scru128 -n 2 | scru128-inspect
{
  "input":        "036ZG552N91MT9S0GYHDWIF95",
  "canonical":    "036ZG552N91MT9S0GYHDWIF95",
  "timestampIso": "2022-03-20T08:34:01.493+00:00",
  "timestamp":    "1647765241493",
  "counterHi":    "10145723",
  "counterLo":    "13179084",
  "entropy":      "4167049657",
  "fieldsHex":    ["017fa6763e95", "9acfbb", "c918cc", "f86021b9"]
}
{
  "input":        "036ZG552N91MT9S0GYJ7I56SJ",
  "canonical":    "036ZG552N91MT9S0GYJ7I56SJ",
  "timestampIso": "2022-03-20T08:34:01.493+00:00",
  "timestamp":    "1647765241493",
  "counterHi":    "10145723",
  "counterLo":    "13179085",
  "entropy":      "3838717859",
  "fieldsHex":    ["017fa6763e95", "9acfbb", "c918cd", "e4ce2fa3"]
}
```

## License

Licensed under the Apache License, Version 2.0.
