"""Command-line interface to generate and inspect SCRU128 identifiers"""

from __future__ import annotations

import argparse
import datetime
import sys

from .. import scru128, Scru128Id


def generate() -> None:
    parser = argparse.ArgumentParser(description="Generate SCRU128 identifiers.")
    parser.add_argument(
        "-n",
        default=1,
        type=int,
        help="generate given number of identifiers",
        metavar="count",
    )

    args = parser.parse_args()
    for _ in range(args.n):
        print(scru128())


def inspect() -> None:
    parser = argparse.ArgumentParser(
        description="Show components of SCRU128 identifiers read from stdin. "
        + "Print a human-readable JSON object for each valid line read."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        type=argparse.FileType("r"),
        help="read identifiers from file",
    )

    args = parser.parse_args()
    try:
        for line in args.file:
            line = line.strip()
            if line != "":
                try:
                    print(_inspect_id(line))
                except ValueError:
                    print("warning: skipped invalid identifier:", line, file=sys.stderr)
    except KeyboardInterrupt:
        sys.exit(1)


def _inspect_id(src: str) -> str:
    obj = Scru128Id.from_str(src)
    timestamp_iso = datetime.datetime.fromtimestamp(
        obj.timestamp / 1000, tz=datetime.timezone.utc
    ).isoformat(timespec="milliseconds")
    fields_hex = '["{:012x}", "{:06x}", "{:06x}", "{:08x}"]'.format(
        obj.timestamp, obj.counter_hi, obj.counter_lo, obj.entropy
    )

    return "\n".join(
        (
            "{",
            f'  "input":        "{src}",',
            f'  "canonical":    "{obj}",',
            f'  "timestampIso": "{timestamp_iso}",',
            f'  "timestamp":    "{obj.timestamp}",',
            f'  "counterHi":    "{obj.counter_hi}",',
            f'  "counterLo":    "{obj.counter_lo}",',
            f'  "entropy":      "{obj.entropy}",',
            f'  "fieldsHex":    {fields_hex}',
            "}",
        )
    )
