"""Command-line interface to generate and inspect SCRU128 identifiers"""

from __future__ import annotations

import argparse
import datetime
import re
import sys

from .. import scru128, Scru128Id, TIMESTAMP_BIAS


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

    pattern = re.compile(r"^[0-7][0-9A-Va-v]{25}$")

    args = parser.parse_args()
    try:
        for line in args.file:
            line = line.strip()
            if line == "":
                continue
            elif pattern.match(line):
                print(_inspect_id(line))
            else:
                print("warning: skipped invalid identifier:", line, file=sys.stderr)
    except KeyboardInterrupt:
        sys.exit(1)


def _inspect_id(src: str) -> str:
    obj = Scru128Id.from_str(src)
    timestamp_iso = datetime.datetime.fromtimestamp(
        (obj.timestamp + TIMESTAMP_BIAS) / 1000, tz=datetime.timezone.utc
    ).isoformat(timespec="milliseconds")
    fields_hex = '["{:011x}", "{:07x}", "{:06x}", "{:08x}"]'.format(
        obj.timestamp, obj.counter, obj.per_sec_random, obj.per_gen_random
    )

    return "\n".join(
        (
            "{",
            f'  "input":        "{src}",',
            f'  "canonical":    "{obj}",',
            f'  "timestampIso": "{timestamp_iso}",',
            f'  "timestamp":    "{obj.timestamp}",',
            f'  "counter":      "{obj.counter}",',
            f'  "perSecRandom": "{obj.per_sec_random}",',
            f'  "perGenRandom": "{obj.per_gen_random}",',
            f'  "fieldsHex":    {fields_hex}',
            "}",
        )
    )
