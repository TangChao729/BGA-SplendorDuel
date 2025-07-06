import pytest
from model.actions import Action, ActionType


def test_action_repr_and_to_dict():
    payload = {"tokens": ["red", "blue"], "level": 1, "index": 2}
    action = Action(ActionType.TAKE_TOKENS, payload)
    # repr includes type name and payload
    r = repr(action)
    assert "TAKE_TOKENS" in r and "'red'" in r
    # to_dict produces correct mapping
    d = action.to_dict()
    assert d["type"] == ActionType.TAKE_TOKENS.value
    assert d["payload"] == payload


def test_action_roundtrip_from_dict():
    original = {
        "type": ActionType.PURCHASE_CARD.value,
        "payload": {"level": 2, "index": 0},
    }
    action = Action.from_dict(original)
    assert isinstance(action, Action)
    assert action.type == ActionType.PURCHASE_CARD
    assert action.payload == original["payload"]
    # round-trip back to dict
    assert action.to_dict() == original


def test_invalid_action_type_in_from_dict():
    bad = {"type": "UNKNOWN_ACTION", "payload": {}}
    with pytest.raises(ValueError):
        Action.from_dict(bad)


def test_default_payload_and_mutability():
    # No payload provided defaults to empty dict
    action = Action(ActionType.REPLENISH_BOARD)
    assert action.payload == {}
    # modifying returned payload should not change original payload (copy semantics)
    d = action.payload
    d["x"] = 1
    assert action.payload.get("x") == 1


def test_use_privilege_action():
    # Example for USE_PRIVILEGE
    action = Action(ActionType.USE_PRIVILEGE, {"colors": ["black", "pearl"]})
    assert action.type == ActionType.USE_PRIVILEGE
    assert action.payload["colors"] == ["black", "pearl"]
