from keep_in_touch.storage.jsonl_store import JsonlStore


def test_jsonl_store_round_trip(tmp_path) -> None:
    path = tmp_path / "people.jsonl"
    store = JsonlStore(path)

    store.write_all([{"id": "p_001", "name": "Jane"}])

    assert store.read_all() == [{"id": "p_001", "name": "Jane"}]


def test_jsonl_store_ignores_blank_lines(tmp_path) -> None:
    path = tmp_path / "people.jsonl"
    path.write_text('\n{"id": "p_001"}\n\n', encoding="utf-8")
    store = JsonlStore(path)

    assert store.read_all() == [{"id": "p_001"}]
