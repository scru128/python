# SCRU128: Sortable, Clock and Random number-based Unique identifier

[![PyPI](https://img.shields.io/pypi/v/scru128)](https://pypi.org/project/scru128/)
[![License](https://img.shields.io/pypi/l/scru128)](https://github.com/scru128/python/blob/main/LICENSE)

SCRU128 ID is yet another attempt to supersede [UUID] in the use cases that need
decentralized, globally unique time-ordered identifiers. SCRU128 is inspired by
[ULID] and [KSUID] and has the following features:

- 128-bit unsigned integer type
- Sortable by generation time (as integer and as text)
- 26-digit case-insensitive portable textual representation
- 44-bit biased millisecond timestamp that ensures remaining life of 550 years
- Up to 268 million time-ordered but unpredictable unique IDs per millisecond
- 84-bit _layered_ randomness for collision resistance

```python
from scru128 import scru128, scru128_string

# generate a new identifier object
x = scru128()
print(x)  # e.g. "00S6GVKR1MH58KE72EJD87SDOO"
print(int(x))  # as a 128-bit unsigned integer

# generate a textual representation directly
print(scru128_string())  # e.g. "00S6GVKR3F7R79I72EJF0J4RGC"
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
00PP7O1FIQFM7C7R8VBK61T94N
$ scru128 -n 4
00PP7OKSN7T37CR12PEIJILTA1
00PP7OKSN7T37CT12PEJKN2BNO
00PP7OKSN7T37CV12PEH41TP72
00PP7OKSN7T37D112PEI1L0HMS
```

`scru128-inspect` prints the components of given SCRU128 IDs as human- and
machine-readable JSON objects.

```bash
$ scru128 -n 2 | scru128-inspect
{
  "input":        "00PP7OUAC22A7TO4VESB1R83L5",
  "canonical":    "00PP7OUAC22A7TO4VESB1R83L5",
  "timestampIso": "2021-10-02T23:38:47.832+00:00",
  "timestamp":    "55381127832",
  "counter":      "34770908",
  "perSecRandom": "1306338",
  "perGenRandom": "3283357349",
  "fieldsHex":    ["00ce4f8f298", "2128fdc", "13eee2", "c3b40ea5"]
}
{
  "input":        "00PP7OUAC22A7TQ4VES9SKQH9U",
  "canonical":    "00PP7OUAC22A7TQ4VES9SKQH9U",
  "timestampIso": "2021-10-02T23:38:47.832+00:00",
  "timestamp":    "55381127832",
  "counter":      "34770909",
  "perSecRandom": "1306338",
  "perGenRandom": "2035107134",
  "fieldsHex":    ["00ce4f8f298", "2128fdd", "13eee2", "794d453e"]
}
```

## License

Licensed under the Apache License, Version 2.0.
