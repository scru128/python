# Changelog

## v2.1.1 - 2022-05-23

### Fixed

- `generate_core()` to reject zero as `timestamp` value

## v2.1.0 - 2022-05-22

### Added

- `generate_core()` and `last_status` to Scru128Generator

## v2.0.0 - 2022-05-01

### Changed

- Textual representation: 26-digit Base32 -> 25-digit Base36
- Field structure: { `timestamp`: 44 bits, `counter`: 28 bits, `per_sec_random`:
  24 bits, `per_gen_random`: 32 bits } -> { `timestamp`: 48 bits, `counter_hi`:
  24 bits, `counter_lo`: 24 bits, `entropy`: 32 bits }
- Timestamp epoch: 2020-01-01 00:00:00.000 UTC -> 1970-01-01 00:00:00.000 UTC
- Counter overflow handling: stall generator -> increment timestamp

### Removed

- `TIMESTAMP_BIAS`
- `Scru128Id#counter()`, `Scru128Id#per_sec_random()`, `Scru128Id#per_gen_random()`

### Added

- `Scru128Id#counter_hi()`, `Scru128Id#counter_lo()`, `Scru128Id#entropy()`

## v1.0.1 - 2022-03-20

### Maintenance

- Updated dev dependencies

## v1.0.0 - 2022-01-03

- Initial stable release
