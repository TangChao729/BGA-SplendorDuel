import pytest
from model.player import PlayerState
from model.cards import Card
from model.tokens import Token


def make_card(
    id="test",
    level=1,
    color="Black",
    points=0,
    bonus=0,
    ability=None,
    crowns=0,
    cost=None,
):
    if cost is None:
        cost = {c: 0 for c in ["black", "red", "green", "blue", "white", "pearl"]}
    return Card(
        id=id,
        level=level,
        color=color,
        points=points,
        bonus=bonus,
        ability=ability,
        crowns=crowns,
        cost=cost,
    )


def test_token_management():
    p = PlayerState("Player 1")
    # Add tokens
    p.add_tokens([Token("black"), Token("black"), Token("gold")])
    assert p.tokens.get(Token("black")) == 2
    assert p.tokens.get(Token("gold")) == 1
    # Remove tokens
    p.remove_tokens({Token("black"): 1, Token("gold"): 1})
    assert p.tokens.get(Token("black")) == 1
    assert p.tokens.get(Token("gold")) == 0
    # Removing too many should assert
    with pytest.raises(AssertionError):
        p.remove_tokens({Token("black"): 5})


def test_can_afford_with_bonus_and_gold():
    p = PlayerState("Player 1")
    # Setup tokens and bonuses
    p.tokens[Token("red")] = 1
    p.bonuses[Token("red")] = 1  # cover cost partially
    p.tokens[Token("gold")] = 1  # wild to cover shortage
    # Card costs 3 red
    card = make_card(
        cost={Token("red"): 3, Token("black"): 0, Token("green"): 0, Token("blue"): 0, Token("white"): 0, Token("pearl"): 0}
    )
    assert p.can_afford(card)
    # If wild insufficient
    p.tokens[Token("gold")] = 0
    assert not p.can_afford(card)


def test_pay_for_card_and_effects():
    p = PlayerState("Player 1")
    # Give tokens
    p.tokens[Token("white")] = 2
    p.tokens[Token("gold")] = 1
    # Card: color white, cost white 2, points 3, crowns 1
    card = make_card(
        id="1",
        color="white",
        points=3,
        crowns=1,
        cost={Token("white"): 2, Token("black"): 0, Token("red"): 0, Token("green"): 0, Token("blue"): 0, Token("pearl"): 0},
    )
    assert p.can_afford(card)
    p.pay_for_card(card)
    # Check tokens used
    assert p.tokens[Token("white")] == 0
    assert p.tokens[Token("gold")] == 1  # no wild used
    # Check purchased
    assert card in p.purchased
    # Bonus incremented
    assert p.bonuses[Token("white")] == 1
    # Points and crowns updated
    assert p.points == 3
    assert p.crowns == 1


def test_reserve_and_privileges():
    p = PlayerState("Player 1")
    card = make_card()
    for i in range(3):
        assert p.reserve_card(card)
    assert len(p.reserved) == 3
    # fourth fails
    assert not p.reserve_card(card)
    # test privileges
    assert not p.use_privilege()
    p.add_privilege(2)
    assert p.privileges == 2
    assert p.use_privilege()
    assert p.privileges == 1


def test_has_won_conditions():
    p = PlayerState()
    # By total points
    p.points = 20
    assert p.has_won()
    # Reset
    p = PlayerState()
    p.crowns = 10
    assert p.has_won()
    # By same-color prestige
    p = PlayerState()
    # Create two cards of color Blue summing 10 points
    c1 = make_card(color="Blue", points=4)
    c2 = make_card(color="Blue", points=6)
    p.purchased = [c1, c2]
    assert p.has_won()
    # Negative case
    p = PlayerState()
    assert not p.has_won()


def test_json_serialization():
    """Test JSON serialization and deserialization of PlayerState."""
    # Create a player with various data
    p = PlayerState("Test Player")
    p.tokens[Token("black")] = 3
    p.tokens[Token("gold")] = 2
    p.bonuses[Token("red")] = 1
    p.privileges = 2
    p.points = 15
    p.crowns = 3
    
    # Add some cards
    card1 = make_card(id="test-1", color="Red", points=5, crowns=1)
    card2 = make_card(id="test-2", color="Blue", points=3)
    p.purchased.append(card1)
    p.reserved.append(card2)
    
    # Serialize to JSON
    json_data = p.to_json()
    assert isinstance(json_data, dict)
    assert json_data["name"] == "Test Player"
    assert json_data["tokens"]["black"] == 3
    assert json_data["bonuses"]["red"] == 1
    assert json_data["privileges"] == 2
    assert len(json_data["purchased"]) == 1
    assert len(json_data["reserved"]) == 1
    
    # Deserialize from JSON
    p2 = PlayerState.from_json(json_data)
    assert p2.name == p.name
    assert p2.tokens == p.tokens
    assert p2.bonuses == p.bonuses
    assert p2.privileges == p.privileges
    assert p2.points == p.points
    assert p2.crowns == p.crowns
    assert len(p2.purchased) == len(p.purchased)
    assert len(p2.reserved) == len(p.reserved)
    assert p2.purchased[0].id == card1.id
    assert p2.reserved[0].id == card2.id


def test_json_file_operations(tmp_path):
    """Test saving and loading PlayerState to/from files."""
    # Create a player with some data
    p = PlayerState("File Test Player")
    p.tokens[Token("white")] = 5
    p.points = 12
    
    # Save to file
    test_file = tmp_path / "player_state.json"
    p.save_to_file(str(test_file))
    
    # Verify file exists and contains JSON
    assert test_file.exists()
    
    # Load from file
    p2 = PlayerState.load_from_file(str(test_file))
    assert p2.name == p.name
    assert p2.tokens[Token("white")] == 5
    assert p2.points == 12


def test_json_with_empty_player():
    """Test JSON operations with a fresh, empty player."""
    p = PlayerState("Empty Player")
    
    # Serialize empty player
    json_data = p.to_json()
    
    # Deserialize and verify defaults
    p2 = PlayerState.from_json(json_data)
    assert p2.tokens[Token("black")] == 0
    assert len(p2.reserved) == 0
    assert len(p2.purchased) == 0
    assert p2.privileges == 0
    assert p2.points == 0
