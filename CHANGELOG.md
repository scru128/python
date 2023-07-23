# Changelog

## v3.0.1 - unreleased

Most notably, v3 switches the letter case of generated IDs from uppercase (e.g.,
"036Z951MHJIKZIK2GSL81GR7L") to lowercase (e.g., "036z951mhjikzik2gsl81gr7l"),
though it is technically not supposed to break existing code because SCRU128 is
a case-insensitive scheme. Other changes include the removal of deprecated APIs.

### Removed

- Deprecated items:
  - `scru128()` and `scru128_string()`
  - `Scru128Generator#generate_core()`
  - `Scru128Generator#last_status` and `Scru128Generator.Status`

### Changed

- Letter case of generated IDs from uppercase to lowercase
- Edge case behavior of generator functions' rollback allowance handling

### Maintenance

- Upgraded minimum supported Python version to 3.8
- Updated dev dependencies

## v2.4.2 - 2023-06-21

### Maintenance

- Updated dev dependencies
- Improved test cases

## v2.4.1 - 2023-04-07

### Maintenance

- Updated dev dependencies
- Tweaked docs and tests

## v2.4.0 - 2023-03-23

### Added

- `generate_or_abort()` and `generate_or_abort_core()` to `Scru128Generator`
  (formerly named as `generate_no_rewind()` and `generate_core_no_rewind()`)
- `Scru128Generator#generate_or_reset_core()`

### Deprecated

- `Scru128Generator#generate_core()`
- `Scru128Generator#last_status` and `Scru128Generator.Status`

## v2.3.1 - 2023-03-19

### Added

- `generate_no_rewind()` and `generate_core_no_rewind()` to `Scru128Generator`
  (experimental)

### Maintenance

- Improved documentation about generator method flavors
- Updated dev dependencies

## v2.3.0 - 2022-12-25

### Added

- Iterable and Iterator implementations to `Scru128Generator` to make it work as
  infinite iterator

### Maintenance

- Updated dev dependencies

## v2.2.0 - 2022-10-30

### Added

- `new()` and `new_string()`

### Deprecated

- `scru128()` and `scru128_string()` to promote `scru128.new()` syntax over
  `from scru128 import scru128`

### Maintenance

- Updated dev dependencies

## v2.1.2 - 2022-06-11

### Fixed

- `generate_core()` to update `counter_hi` when `timestamp` passed < 1000

### Maintenance

- Updated dev dependencies

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
