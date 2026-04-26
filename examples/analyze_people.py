"""Example analysis for Keep in Touch JSONL data.

Run from the repository root:

    python examples/analyze_people.py examples/demo_data/people.jsonl

The script uses only the Python standard library to show that Keep in Touch data
is easy to inspect, aggregate, and prepare for deeper analysis.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def main() -> int:
    """Parse command-line arguments and print analysis results."""

    args = parse_args()
    people = load_people(args.people_path)
    today = date.fromisoformat(args.today)
    print_report(people, today)
    return 0


def parse_args() -> argparse.Namespace:
    """Return parsed command-line arguments."""

    parser = argparse.ArgumentParser(description="Analyze Keep in Touch people data.")
    parser.add_argument(
        "people_path",
        type=Path,
        nargs="?",
        default=Path("examples/demo_data/people.jsonl"),
        help="Path to a people JSONL file.",
    )
    parser.add_argument(
        "--today",
        default="2026-04-26",
        help="Analysis date in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def load_people(path: Path) -> list[dict[str, Any]]:
    """Load people records from a JSON Lines file."""

    people: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if stripped:
                people.append(json.loads(stripped))
    return people


def print_report(people: list[dict[str, Any]], today: date) -> None:
    """Print a compact report from people records."""

    print(f"People analyzed: {len(people)}")
    print(f"Analysis date:   {today.isoformat()}")
    print()
    print_counter("Relationships", relationship_counts(people))
    print_counter("Preferred contact methods", preferred_method_counts(people))
    print_counter("Most common tags", tag_counts(people), limit=10)
    print_counter("Social platform coverage", social_platform_counts(people))
    print_contact_field_coverage(people)
    print_upcoming_birthdays(people, today, limit=5)
    print_contact_age_summary(people, today)
    print_stale_contacts(people, today, limit=5)


def relationship_counts(people: list[dict[str, Any]]) -> Counter[str]:
    """Return counts by relationship category."""

    return Counter(record.get("relationship") or "Unknown" for record in people)


def preferred_method_counts(people: list[dict[str, Any]]) -> Counter[str]:
    """Return counts by preferred contact method."""

    return Counter(
        record.get("preferred_contact_method") or "not set" for record in people
    )


def tag_counts(people: list[dict[str, Any]]) -> Counter[str]:
    """Return counts for all tags."""

    counts: Counter[str] = Counter()
    for record in people:
        counts.update(str(tag) for tag in record.get("tags", []))
    return counts


def social_platform_counts(people: list[dict[str, Any]]) -> Counter[str]:
    """Return counts for social platforms with saved handles."""

    counts: Counter[str] = Counter()
    for record in people:
        socials = record.get("socials", {})
        if isinstance(socials, dict):
            counts.update(key for key, value in socials.items() if value)
    return counts


def print_contact_field_coverage(people: list[dict[str, Any]]) -> None:
    """Print coverage for direct contact fields."""

    total = len(people)
    email_count = sum(1 for record in people if record.get("email"))
    phone_count = sum(1 for record in people if record.get("phone"))
    print("Direct contact coverage:")
    print(f"  email: {email_count}/{total}")
    print(f"  phone: {phone_count}/{total}")
    print()


def print_upcoming_birthdays(
    people: list[dict[str, Any]],
    today: date,
    limit: int,
) -> None:
    """Print the next upcoming birthdays."""

    upcoming = [
        (days_until_birthday(record, today), full_name(record))
        for record in people
        if days_until_birthday(record, today) is not None
    ]
    upcoming.sort()

    print(f"Next {limit} birthdays:")
    if not upcoming:
        print("  -")
        print()
        return
    for days, name in upcoming[:limit]:
        label = "today" if days == 0 else f"in {days} days"
        print(f"  {name}: {label}")
    print()


def print_counter(title: str, counts: Counter[str], limit: int | None = None) -> None:
    """Print a sorted counter section."""

    print(f"{title}:")
    items = counts.most_common(limit)
    if not items:
        print("  -")
    for label, count in items:
        print(f"  {label}: {count}")
    print()


def print_contact_age_summary(people: list[dict[str, Any]], today: date) -> None:
    """Print summary statistics for days since last contact."""

    ages = [
        days_since_contact(record, today)
        for record in people
        if days_since_contact(record, today) is not None
    ]
    never_contacted = len(people) - len(ages)
    print("Contact age:")
    print(f"  never contacted: {never_contacted}")
    if not ages:
        print("  no dated contacts")
        print()
        return

    average_age = sum(ages) / len(ages)
    print(f"  average days since contact: {average_age:.1f}")
    print(f"  oldest contact age:         {max(ages)} days")
    print(f"  newest contact age:         {min(ages)} days")
    print()


def print_stale_contacts(
    people: list[dict[str, Any]],
    today: date,
    limit: int,
) -> None:
    """Print people with the oldest known contact dates."""

    dated_people = [
        (days_since_contact(record, today), full_name(record))
        for record in people
        if days_since_contact(record, today) is not None
    ]
    dated_people.sort(reverse=True)

    print(f"Oldest {limit} known contacts:")
    for age, name in dated_people[:limit]:
        print(f"  {name}: {age} days")
    print()


def days_since_contact(record: dict[str, Any], today: date) -> int | None:
    """Return days since last contact for a raw person record."""

    raw_date = record.get("last_contacted_at")
    if not isinstance(raw_date, str) or not raw_date:
        return None
    last_contacted = date.fromisoformat(raw_date)
    return max(0, (today - last_contacted).days)


def days_until_birthday(record: dict[str, Any], today: date) -> int | None:
    """Return days until the next birthday for a raw person record."""

    raw_birthday = record.get("birthday")
    if not isinstance(raw_birthday, str) or not raw_birthday:
        return None
    birthday = date.fromisoformat(raw_birthday)
    next_birthday = birthday_for_year(birthday, today.year)
    if next_birthday < today:
        next_birthday = birthday_for_year(birthday, today.year + 1)
    return (next_birthday - today).days


def birthday_for_year(birthday: date, year: int) -> date:
    """Return this year's birthday, moving Feb 29 to Mar 1 when needed."""

    try:
        return date(year, birthday.month, birthday.day)
    except ValueError:
        return date(year, 3, 1)


def full_name(record: dict[str, Any]) -> str:
    """Return a display name for a raw person record."""

    parts = [
        record.get("first_name", ""),
        record.get("middle_name", ""),
        record.get("last_name", ""),
    ]
    name = " ".join(str(part).strip() for part in parts if str(part).strip())
    return name or "(Unnamed)"


if __name__ == "__main__":
    raise SystemExit(main())
