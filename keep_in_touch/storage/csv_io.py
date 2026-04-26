"""CSV import/export helpers."""

import csv
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fieldnames: list[str]) -> None:
    """Write dictionaries to a CSV file.

    Args:
        path: Output file.
        rows: Records to write.
        fieldnames: Column order.

    Example:
        write_csv(Path("people.csv"), [{"name": "Jane"}], ["name"])
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_flatten_row(row, fieldnames))


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file as a list of dictionaries.

    Example:
        rows = read_csv(Path("people.csv"))
        assert isinstance(rows, list)
    """

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def _flatten_row(row: Mapping[str, Any], fieldnames: list[str]) -> dict[str, str]:
    """Convert nested/list values to simple CSV-friendly text."""

    flat: dict[str, str] = {}
    for key in fieldnames:
        value = row.get(key, "")
        if isinstance(value, list):
            flat[key] = ", ".join(str(item) for item in value)
        elif value is None:
            flat[key] = ""
        else:
            flat[key] = str(value)
    return flat
