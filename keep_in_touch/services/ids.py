"""ID generation helpers."""

from uuid import uuid4


def new_person_id() -> str:
    """Return a new person ID.

    Example:
        assert new_person_id().startswith("p_")
    """

    return f"p_{uuid4().hex[:12]}"


def new_interaction_id() -> str:
    """Return a new interaction ID.

    Example:
        assert new_interaction_id().startswith("i_")
    """

    return f"i_{uuid4().hex[:12]}"
