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
print(x)  # e.g., "036z951mhjikzik2gsl81gr7l"
print(int(x))  # as a 128-bit unsigned integer

# generate a textual representation directly
print(scru128.new_string())  # e.g., "036z951mhzx67t63mq9xe6q0j"
```

See [SCRU128 Specification] for details.

[UUID]: https://en.wikipedia.org/wiki/Universally_unique_identifier
[ULID]: https://github.com/ulid/spec
[KSUID]: https://github.com/segmentio/ksuid
[SCRU128 Specification]: https://github.com/scru128/spec

## Command-line interface

`scru128` generates SCRU128 IDs.

```bash
$ scru128
036zg4zlmdwdz8414eim77vct
$ scru128 -n 4
036zg4zlv707wnczl108ky4i7
036zg4zlv707wnczl12towmho
036zg4zlv707wnczl14hirm6n
036zg4zlv707wnczl17110shh
```

`scru128-inspect` prints the components of given SCRU128 IDs as human- and
machine-readable JSON objects.

```bash
$ scru128 -n 2 | scru128-inspect
{
  "input":        "036zg552n91mt9s0gyhdwif95",
  "canonical":    "036zg552n91mt9s0gyhdwif95",
  "timestampIso": "2022-03-20T08:34:01.493+00:00",
  "timestamp":    "1647765241493",
  "counterHi":    "10145723",
  "counterLo":    "13179084",
  "entropy":      "4167049657",
  "fieldsHex":    ["017fa6763e95", "9acfbb", "c918cc", "f86021b9"]
}
{
  "input":        "036zg552n91mt9s0gyj7i56sj",
  "canonical":    "036zg552n91mt9s0gyj7i56sj",
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
