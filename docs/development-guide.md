# Development Guide

This guide is for someone who wants to understand, fix, or extend Keep in Touch.
The app is intentionally split into small layers so most changes have a
predictable path through the codebase.

## Big Picture

Keep in Touch is a local-first PySide6 desktop app. It loads plain JSONL files
from a user-selected data folder, turns those records into Python dataclasses,
shows them in a sortable/filterable table, and writes changes back to JSONL.

The startup path is:

```text
run_app.py
-> keep_in_touch.app.main.main()
-> MainWindow
-> services configured from AppConfig
-> people and interactions loaded from JSONL stores
-> UI widgets render the current in-memory data
```

The most useful mental model is:

```text
storage files -> domain models -> services -> UI widgets/dialogs
```

The UI should ask services to perform app workflows. The services should work
with domain models and storage. Domain helpers should stay independent of
PySide6 where possible so they are easy to test.

## Project Map

`keep_in_touch/domain/`

Core data structures and pure helper logic. Start here when you want to know
what a person or interaction is. This layer should not import PySide6.

- `models.py`: `Person` and `Interaction` dataclasses plus option lists.
- `serialization.py`: converts between dataclasses and JSONL dictionaries.
- `validation.py`: normalizes user/file input.
- `date_utils.py`: date parsing and current-date helpers.
- `display.py`: display-friendly text helpers.
- `formulas.py`: contact interval and urgency calculations.
- `person_filters.py`: pure people-list filtering logic.

`keep_in_touch/storage/`

File-level persistence. This layer knows about files, paths, JSONL, CSV, app
settings, and backups. It should not know about widgets.

- `jsonl_store.py`: generic JSON Lines load/save helper.
- `app_paths.py`: expected data-folder layout.
- `app_settings.py`: remembered data directory.
- `csv_io.py`: CSV helpers.
- `backup.py`: backup helpers.

`keep_in_touch/services/`

Application workflows. This layer coordinates domain objects and storage.
Services are where you put logic like "logging an interaction should update the
person's last-contacted date."

- `people_service.py`: create, update, delete, list people.
- `interaction_service.py`: log, edit, delete interactions and recalculate
  related person contact dates.
- `import_export_service.py`: CSV/JSONL import and export.
- `ids.py`: ID generation.

`keep_in_touch/ui/`

PySide6 widgets and dialogs. This layer owns layout, buttons, tables, text
panels, menus, and user prompts.

- `main_window.py`: top-level window, menus, action state, filtering, selection.
- `people_table.py`: sortable people table and table-cell decoration.
- `person_detail_panel.py`: copy-friendly ASCII detail view.
- `app_icon.py`: packaged application icon loader.
- `dialogs/`: add/edit person, edit socials, log/edit interactions.

`keep_in_touch/app/`

Startup and runtime configuration.

- `main.py`: creates `QApplication`, sets the app icon, opens the main window.
- `app_config.py`: paths derived from the selected data folder.

`tests/`

Focused behavior tests. These are mostly domain/service tests because those are
the easiest and most valuable pieces to test without launching a full GUI.

`examples/`

Demo data and small analysis scripts. `examples/demo_data` is a complete data
folder you can select from the app.

## How Data Moves

At startup, `MainWindow` asks `AppConfig` whether a data folder is configured.
If it is, the window creates:

```python
PeopleService(JsonlStore(config.people_path))
InteractionService(JsonlStore(config.interactions_path), people_service)
ImportExportService(people_service, interaction_service)
```

When the people list refreshes, `PeopleService.list_people()` returns
`list[Person]`. The main window stores that full list as `self.people`. The
current filters produce `self.filtered_people`, and `PeopleTable.set_people()`
redraws the visible table rows.

When you select a row, the table emits the selected person ID. The main window
finds that person in `self.people`, asks `InteractionService` for that person's
interaction history, and passes both objects to `PersonDetailPanel`.

When you log an interaction, the main window opens `LogInteractionDialog`, then
passes the validated values to `InteractionService.log_interaction()`. The
service writes the interaction and updates the person's `last_contacted_at`.

## Common Change Paths

### Change the Main Table

Edit `keep_in_touch/ui/people_table.py`.

Most table columns are defined in `PeopleTable.COLUMNS`. A column needs:

- display text
- width
- sort value
- optional decoration

If you add a column, also check `MainWindow.preferred_initial_size()` because
the startup width is based on the table's preferred width.

### Change Filtering

Filtering is split between the UI and pure domain logic.

- UI controls live in `MainWindow._create_filter_panel()`.
- Current UI values become `PeopleFilterCriteria` in
  `MainWindow._filter_criteria()`.
- Matching logic lives in `keep_in_touch/domain/person_filters.py`.

Search filtering builds a lowercase string from selected person fields and does
substring matching. Date and birthday filters use real `date` values.

Add or update tests in `tests/test_person_filters.py` when changing filter
behavior.

### Change the Detail Pane

Edit `keep_in_touch/ui/person_detail_panel.py`.

The detail pane is deliberately text-first. It uses `QTextEdit` so the full
record is selectable and copyable. The ASCII rendering is ordinary Python string
formatting, which keeps the pane easy to change without managing many nested
widgets.

If you add data to the detail pane, prefer adding it to the relevant section in
`person_detail_text()`.

### Change Add/Edit Person Fields

For first-class stored fields, follow [Adding a New Field](adding-new-field.md).

For UI-only rearrangement, edit `keep_in_touch/ui/dialogs/edit_person_dialog.py`.
The important methods are:

- `__init__`: creates widgets and lays out the form.
- `accept`: validates before closing.
- `to_person`: returns a `Person` object from the form fields.

### Change Interaction Logging

Start with:

- `keep_in_touch/ui/dialogs/log_interaction_dialog.py`
- `keep_in_touch/services/interaction_service.py`

The dialog collects and validates user input. The service owns the workflow:
write the interaction, update/recalculate the related person's contact state,
and persist the data.

### Change Import or Export

Edit `keep_in_touch/services/import_export_service.py`.

CSV field order and aliases live there. JSONL behavior usually depends on
`domain/serialization.py`.

### Change Storage Paths or Data Folder Setup

Start with:

- `keep_in_touch/app/app_config.py`
- `keep_in_touch/storage/app_paths.py`
- `keep_in_touch/storage/app_settings.py`

The app should continue to open without a configured data folder. In that state,
data actions are disabled until the user selects a folder.

## Debugging Workflow

1. Reproduce with demo data if possible.

   Open the app and select `examples/demo_data` as the data folder. This gives
   you a stable set of people and interactions without touching private data.

2. Find the layer where the bug belongs.

   - Wrong value saved or loaded: `domain/serialization.py` or `storage/`.
   - Workflow side effect wrong: `services/`.
   - Table display/sorting wrong: `ui/people_table.py`.
   - Filtering wrong: `domain/person_filters.py` and `MainWindow`.
   - Dialog validation/form issue: `ui/dialogs/`.
   - Detail text wrong: `ui/person_detail_panel.py`.

3. Prefer a small pure test when possible.

   If the behavior can be tested without a window, put the test in `tests/`.
   Filtering, serialization, formulas, and services are all good test targets.

4. Run a compile check.

   ```bash
   python -m compileall -q keep_in_touch tests examples
   ```

5. Run tests if available.

   ```bash
   python -m pytest -q
   ```

6. Smoke test the app.

   ```bash
   python run_app.py
   ```

## Useful Commands

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the app:

```bash
python run_app.py
```

Run compile checks:

```bash
python -m compileall -q keep_in_touch tests examples
```

Run tests:

```bash
python -m pytest -q
```

Run linting and typing if the tools are installed:

```bash
ruff check .
mypy keep_in_touch tests
```

Analyze example data:

```bash
python examples/analyze_people.py
```

## Maintenance Guidelines

Keep the layers separated. UI code can import services and domain helpers, but
domain code should stay free of PySide6. This keeps core behavior testable.

Keep stored data boring. JSONL records should use plain strings, numbers, lists,
dictionaries, booleans, and ISO date strings. Avoid storing UI-specific text.

Preserve unknown fields. The serialization layer keeps unrecognized fields in
`extra_fields` so older/newer data can survive round trips.

Keep UI changes small and local. Desktop layouts can become hard to maintain if
one widget owns everything. If a section becomes complex, consider moving it to
a dedicated widget or dialog.

Prefer pure helpers for logic. Filtering, display text, date parsing, and
calculations are easier to understand and test when they live outside widgets.

Do not silently discard user data. If you change schema behavior, add a test
that proves old data still loads and new data writes predictably.

## Where to Start as a New Contributor

Read these files in order:

1. `keep_in_touch/domain/models.py`
2. `keep_in_touch/domain/serialization.py`
3. `keep_in_touch/storage/jsonl_store.py`
4. `keep_in_touch/services/people_service.py`
5. `keep_in_touch/services/interaction_service.py`
6. `keep_in_touch/app/main.py`
7. `keep_in_touch/ui/main_window.py`
8. `keep_in_touch/ui/people_table.py`
9. `keep_in_touch/ui/person_detail_panel.py`

After that, pick one narrow workflow, such as "edit a person" or "log an
interaction", and trace it from the button click to the service call to the file
write. That is the fastest way to build a working mental model of the app.
