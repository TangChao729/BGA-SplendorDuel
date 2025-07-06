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
    p = PlayerState()
    # Add tokens
    p.add_tokens([Token("black"), Token("black"), Token("gold")])
    assert p.tokens.get("black") == 2
    assert p.tokens.get("gold") == 1
    # Remove tokens
    p.remove_tokens({"black": 1, "gold": 1})
    assert p.tokens.get("black") == 1
    assert p.tokens.get("gold") == 0
    # Removing too many should assert
    with pytest.raises(AssertionError):
        p.remove_tokens({"black": 5})


def test_can_afford_with_bonus_and_gold():
    p = PlayerState()
    # Setup tokens and bonuses
    p.tokens["red"] = 1
    p.bonuses["red"] = 1  # cover cost partially
    p.tokens["gold"] = 1  # wild to cover shortage
    # Card costs 3 red
    card = make_card(
        cost={"red": 3, "black": 0, "green": 0, "blue": 0, "white": 0, "pearl": 0}
    )
    assert p.can_afford(card)
    # If wild insufficient
    p.tokens["gold"] = 0
    assert not p.can_afford(card)


def test_pay_for_card_and_effects():
    p = PlayerState()
    # Give tokens
    p.tokens["white"] = 2
    p.tokens["gold"] = 1
    # Card: color white, cost white 2, points 3, crowns 1
    card = make_card(
        id="1",
        color="white",
        points=3,
        crowns=1,
        cost={"white": 2, "black": 0, "red": 0, "green": 0, "blue": 0, "pearl": 0},
    )
    assert p.can_afford(card)
    p.pay_for_card(card)
    # Check tokens used
    assert p.tokens["white"] == 0
    assert p.tokens["gold"] == 1  # no wild used
    # Check purchased
    assert card in p.purchased
    # Bonus incremented
    assert p.bonuses["white"] == 1
    # Points and crowns updated
    assert p.points == 3
    assert p.crowns == 1


def test_reserve_and_privileges():
    p = PlayerState()
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
