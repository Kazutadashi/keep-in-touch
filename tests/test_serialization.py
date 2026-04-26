from keep_in_touch.domain.serialization import person_from_record, person_to_record


def test_person_socials_round_trip() -> None:
    person = person_from_record(
        {
            "id": "p_001",
            "first_name": "Jane",
            "socials": {
                "discord": "jane#1234",
                "matrix": "@jane:matrix.org",
                "empty": "",
            },
        }
    )

    assert person.socials == {
        "discord": "jane#1234",
        "matrix": "@jane:matrix.org",
    }
    assert person_to_record(person)["socials"] == person.socials


def test_person_contact_fields_round_trip() -> None:
    person = person_from_record(
        {
            "id": "p_002",
            "first_name": "Jane",
            "middle_name": "Alex",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "+1-555-0199",
        }
    )

    record = person_to_record(person)

    assert person.middle_name == "Alex"
    assert person.full_name == "Jane Alex Doe"
    assert record["middle_name"] == "Alex"
    assert record["email"] == "jane@example.com"
    assert record["phone"] == "+1-555-0199"
