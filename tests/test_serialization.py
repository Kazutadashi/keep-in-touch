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
