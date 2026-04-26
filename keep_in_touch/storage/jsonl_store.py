"""Generic JSON Lines storage."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JsonlStore:
    """Read and write newline-delimited JSON records.

    Args:
        path: File path to read and write.

    Example:
        store = JsonlStore(Path("people.jsonl"))
        store.write_all([{"id": "p_001", "name": "Jane"}])
        records = store.read_all()
        assert records[0]["id"] == "p_001"
    """

    def __init__(self, path: Path) -> None:
        """Create a store for a JSONL file path."""

        self.path = path

    def read_all(self) -> list[dict[str, Any]]:
        """Read all records from the JSONL file.

        Blank lines are ignored. Invalid JSON raises a ValueError with line context.
        """

        if not self.path.exists():
            return []

        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    value = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    msg = f"Invalid JSON in {self.path} on line {line_number}: {exc}"
                    raise ValueError(msg) from exc
                if not isinstance(value, dict):
                    msg = f"Expected object in {self.path} on line {line_number}"
                    raise ValueError(msg)
                records.append(value)
        return records

    def write_all(self, records: list[dict[str, Any]]) -> None:
        """Atomically write all records to disk.

        A temporary file is written first, then moved into place. This reduces the
        chance of a corrupted file if the app exits during a save.
        """

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_name = ""
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                delete=False,
                newline="\n",
            ) as temp_file:
                temp_name = temp_file.name
                for record in records:
                    encoded_record = json.dumps(
                        record,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    temp_file.write(encoded_record)
                    temp_file.write("\n")
            os.replace(temp_name, self.path)
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)

    def append(self, record: dict[str, Any]) -> None:
        """Append one record.

        This method is convenient for scripts. Core app services often prefer
        read-modify-write workflows so related files can be kept consistent.
        """

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file.write("\n")
