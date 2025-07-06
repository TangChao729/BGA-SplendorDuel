import os
import json
import pytest
from model.cards import Royal

# Path to royals.json
ROOT = os.path.dirname(os.path.dirname(__file__))
ROYALS_PATH = os.path.join(ROOT, "data", "royals.json")


def test_royal_from_dict():
    data = {"id": "royal_1", "points": 2, "ability": "steal"}
    royal = Royal.from_dict(data)
    assert royal.id == "royal_1"
    assert royal.points == 2
    assert royal.ability == "steal"
    # Test to_dict
    d = royal.to_dict()
    assert d == data


def test_load_royals_json():
    # Ensure the file exists
    assert os.path.isfile(ROYALS_PATH), f"Royals file not found at {ROYALS_PATH}"
    with open(ROYALS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    assert "royals" in raw and isinstance(raw["royals"], list)
    royals_list = raw["royals"]
    # Expect 4 royals as defined
    assert len(royals_list) == 4
    # Convert to Royal objects and validate
    royals = [Royal.from_dict(entry) for entry in royals_list]
    # Check unique IDs and that to_dict round-trips
    ids = set(r.id for r in royals)
    assert len(ids) == 4  # all unique
    for entry, royal in zip(royals_list, royals):
        assert royal.to_dict() == entry
