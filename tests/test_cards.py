import json
import random
import pytest
from model.cards import Card, Deck, Royal, Pyramid
from model.tokens import Token


@pytest.fixture
def temp_path(tmp_path):
    return tmp_path


def test_create_card_from_dict():
    data = {
        "id": "1-01",
        "level": 1,
        "color": "Red",
        "points": 1,
        "bonus": 1,
        "ability": None,
        "crowns": 0,
        "cost": {
            "black": 1,
            "red": 0,
            "green": 0,
            "blue": 0,
            "white": 0,
            "pearl": 0,
        },
    }
    c = Card.from_dict(data)
    # Check attributes
    assert c.id == "1-01"
    assert c.level == 1
    assert c.color == "Red"
    assert c.points == 1
    assert c.bonus == 1
    assert c.ability is None
    assert c.crowns == 0
    assert c.cost == {
        Token("black"): 1,
        Token("red"): 0,
        Token("green"): 0,
        Token("blue"): 0,
        Token("white"): 0,
        Token("pearl"): 0,
    }
    # Round-trip to dict
    assert c.to_dict() == data


def test_deck_from_json(temp_path):
    # Create a minimal deck.json with exactly required counts
    data = {
        "cards": [
            {
                "id": f"{lvl}-{i+1:02d}",
                "level": lvl,
                "color": "Black",
                "points": 0,
                "bonus": 0,
                "ability": None,
                "crowns": 0,
                "cost": {
                    "black": 0,
                    "red": 0,
                    "green": 0,
                    "blue": 0,
                    "white": 0,
                    "pearl": 0,
                },
            }
            for lvl, count in [(1, 5), (2, 4), (3, 3)]
            for i in range(count)
        ]
    }
    deck_json = json.dumps(data)
    # Write to a temporary file
    deck_path = temp_path / "deck.json"
    deck_path.write_text(deck_json)

    # Load the deck
    deck = Deck.from_json(str(deck_path))
    assert len(deck) == 12
    assert isinstance(deck._cards[0], Card)


def test_deck_draw_peek_add_len():
    # Create 5 distinct cards
    cards = [Card(str(i), 1, "Blue", 0, 0, None, 0, {}) for i in range(5)]
    random.seed(42)
    deck = Deck(cards)
    initial_len = len(deck)
    # Peek does not remove
    peeked = deck.peek(3)
    assert len(deck) == initial_len
    assert peeked == deck.peek(3)
    # Draw 2 cards
    drawn = deck.draw(2)
    assert len(drawn) == 2
    assert len(deck) == initial_len - 2
    # Add cards back
    deck.add_cards(drawn)
    assert len(deck) == initial_len


def test_royal_roundtrip_and_repr(tmp_path):
    data = {"id": "royal_1", "points": 3, "ability": "steal"}
    royal = Royal.from_dict(data)
    assert royal.id == data["id"]
    assert royal.points == data["points"]
    assert royal.ability == data["ability"]
    # to_dict
    assert royal.to_dict() == data
    # repr contains essential fields
    repr_str = repr(royal)
    assert data["id"] in repr_str and str(data["points"]) in repr_str

    # Test from_json
    royals_json = tmp_path / "royals.json"
    royals_json.write_text(json.dumps({"royals": [data]}))
    royals = Royal.from_json(str(royals_json))
    assert len(royals) == 1
    assert royals[0].id == data["id"]


def test_pyramid_slot_counts_repr_get_fill_card():
    # Prepare decks with predictable cards
    lvl1 = [Card(f"1-{i}", 1, "Green", 0, 0, None, 0, {}) for i in range(1, 8)]
    lvl2 = [Card(f"2-{i}", 2, "Red", 0, 0, None, 0, {}) for i in range(1, 7)]
    lvl3 = [Card(f"3-{i}", 3, "Blue", 0, 0, None, 0, {}) for i in range(1, 6)]
    decks = {1: Deck(lvl1), 2: Deck(lvl2), 3: Deck(lvl3)}
    pyr = Pyramid(decks)
    # Check slot lengths
    assert len(pyr.slots[1]) == 5
    assert len(pyr.slots[2]) == 4
    assert len(pyr.slots[3]) == 3
    # __repr__ contains each level label
    repr_str = repr(pyr)
    assert "L1" in repr_str and "L2" in repr_str and "L3" in repr_str

    # Get a card
    card = pyr.get_card(1, 0)  # get first card of level 1
    assert card.id.startswith("1-")  # Should be a level 1 card

    # number of card in level 1 should be 5 now
    assert len(pyr.slots[1]) == 5

    # Get a card that doesn't exist
    assert pyr.get_card(1, 0) is None  # Should return None if slot is empty

    # Fill a card
    pyr.fill_card(1, 0)  # Replace first card of level 1
    assert len(pyr.slots[1]) == 5  # Should still have 5 cards

    # to and from dict
    dict_repr = pyr.to_dict()
    assert isinstance(dict_repr, dict)
    back_from_dict = Pyramid.from_dict(dict_repr)
    assert isinstance(back_from_dict, Pyramid)

    # check the instance is the same
    assert repr(back_from_dict) == repr(pyr)
