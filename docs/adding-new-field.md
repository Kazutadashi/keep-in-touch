# Adding a New Field

This guide explains how to add a new first-class field to Keep in Touch without breaking existing JSONL data. It uses a person field as the main example because people records touch the most parts of the app: the domain model, serialization, CSV import/export, edit dialog, detail panel, examples, and tests.

The most important rule is that the stored data should remain simple. Prefer plain strings, ISO date strings, numbers, booleans, lists, or dictionaries with stable keys. Keep in Touch is designed so the files can be loaded into Python, pandas, scikit-learn workflows, or small standard-library scripts without reverse-engineering UI text.

## 1. Choose the Stored Field Name

Use a stable snake_case field name that describes the data rather than the widget that edits it. Good examples are `middle_name`, `email`, `phone`, `birthday`, and `preferred_contact_method`. Avoid names that encode a temporary UI decision, such as `sidebar_text` or `dialog_value`.

Decide the type before editing code. A short optional text value should usually be a `str` with an empty-string default. A date should be a `date | None` in Python and an ISO `YYYY-MM-DD` string in JSONL. Repeating labels should usually be `list[str]`. Flexible keyed data, such as social handles, can be `dict[str, str]`.

## 2. Add the Field to the Domain Model

Edit `keep_in_touch/domain/models.py` and add the field to the relevant dataclass. For a new person text field, add it to `Person` with a conservative default.

```python
@dataclass
class Person:
    id: str
    first_name: str
    middle_name: str = ""
    last_name: str = ""
    email: str = ""
```

If the field affects display or sorting, update the relevant property in the same file. For example, `middle_name` belongs in `full_name` and `sort_name`, while `email` does not.

## 3. Update Serialization

Edit `keep_in_touch/domain/serialization.py`. Add the new key to `PERSON_FIELDS` so it is treated as a known schema field rather than preserved as an unknown extra field.

```python
PERSON_FIELDS = {
    "id",
    "first_name",
    "middle_name",
    "last_name",
}
```

Then read the field in `person_from_record` and write it in `person_to_record`.

```python
return Person(
    id=normalize_text(record.get("id")),
    first_name=normalize_text(record.get("first_name")),
    middle_name=normalize_text(record.get("middle_name")),
)
```

```python
record.update(
    {
        "id": person.id,
        "first_name": person.first_name,
        "middle_name": person.middle_name,
    }
)
```

This does not break older JSONL files. If an older record does not have the new key, the normal default is used. If you are promoting an older `extra_fields` value into a first-class field, read both names during migration, as `middle_name` currently does with the legacy `middle` key.

## 4. Add Validation or Normalization

Most simple text fields can use `normalize_text` from `keep_in_touch/domain/validation.py`. If the new field has structure, add a small normalizer there rather than scattering cleanup logic through UI and services. The goal is that records loaded from JSONL, CSV, or tests all pass through the same cleanup path.

For dates, use the helpers in `keep_in_touch/domain/date_utils.py`. Python code should work with `date | None`; JSONL should store ISO strings.

## 5. Expose the Field in the Edit Dialog

Edit `keep_in_touch/ui/dialogs/edit_person_dialog.py`. Add a widget in `__init__`, place it in the form, and include the value in `to_person`.

```python
self.email_edit = QLineEdit(person.email if person else "")
form.addRow("Email", self.email_edit)
```

```python
return Person(
    id=existing.id if existing else "",
    first_name=self.first_name_edit.text().strip(),
    email=self.email_edit.text().strip(),
)
```

Keep the widget appropriate to the data. Use a line edit for short text, a combo box for controlled categories, a date edit for dates, and a dedicated dialog when a field would otherwise dominate the form.

## 6. Show the Field Where It Helps Users

Edit `keep_in_touch/ui/person_detail_panel.py` if the field should appear in the detail pane. Add it to the most relevant section and keep the label human-readable.

```python
_field("Email", person.email)
```

If the field belongs in the table, update `keep_in_touch/ui/people_table.py` by adding a `PeopleTableColumn`. Every table column needs display text and a sort value. For data-science-friendly fields, prefer simple display values and explicit sort values.

## 7. Update Import and Export

Edit `keep_in_touch/services/import_export_service.py`. Add the new field to `PEOPLE_CSV_FIELDS` if it should be included in CSV export.

```python
PEOPLE_CSV_FIELDS = [
    "id",
    "first_name",
    "email",
]
```

If users may import the field under common alternate names, add aliases in `_normalize_people_csv_row`.

```python
aliases = {
    "email_address": "email",
    "e_mail": "email",
}
```

JSONL export usually works automatically once `person_to_record` writes the new field.

## 8. Update Examples and Analysis

Keep `examples/demo_data/people.jsonl` useful as a real app data folder. If the new field matters for demonstration or analysis, add it to the example records. If the field is relevant to analytics, update `examples/analyze_people.py` with a small statistic or display so the project continues to prove that its data is easy to use outside the UI.

For example, direct contact fields are summarized as coverage counts:

```python
email_count = sum(1 for record in people if record.get("email"))
phone_count = sum(1 for record in people if record.get("phone"))
```

## 9. Add or Update Tests

At minimum, add a serialization round-trip test in `tests/test_serialization.py` for the new field. This protects both old-file loading and new-file writing.

```python
def test_person_email_round_trip() -> None:
    person = person_from_record(
        {
            "id": "p_001",
            "first_name": "Jane",
            "email": "jane@example.com",
        }
    )

    record = person_to_record(person)

    assert person.email == "jane@example.com"
    assert record["email"] == "jane@example.com"
```

If the field affects computed display, sorting, or service behavior, add focused tests for those modules too. Keep tests small and close to the behavior they protect.

## 10. Verify the Change

Run a compile check after editing Python files.

```bash
python -m compileall -q keep_in_touch tests examples
```

If `pytest` is installed, run the test suite.

```bash
python -m pytest -q
```

Finally, run the example analysis script if the field affects examples or analytics.

```bash
python examples/analyze_people.py
```

## Checklist

Before calling a new field complete, confirm that the dataclass has the field, serialization reads and writes it, CSV import/export handles it when appropriate, the edit dialog can modify it, the detail panel or table shows it if useful, examples remain representative, and tests cover the expected round trip. This sounds like a lot, but each step is small, and following the same path every time keeps the app easy to extend without turning the data model into guesswork.
