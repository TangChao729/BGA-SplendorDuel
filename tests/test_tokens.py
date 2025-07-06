import os
import pytest
from model.tokens import Bag, Token, Board
import json


def test_token_repr_and_todict():
    # Test for a normal token (pearl) and wildcard (gold)
    pearl = Token("pearl")
    gold = Token("gold")
    assert "pearl" in repr(pearl) and "🟣" in repr(pearl)
    assert pearl.to_dict() == {"color": "pearl"}
    assert "gold" in repr(gold) and "🟡" in repr(gold)
    assert gold.to_dict() == {"color": "gold"}


def test_bag_basic_draw_return_counts_repr(tmp_path):
    # Initialize bag with known counts
    initial = {"black": 2, "pearl": 1, "gold": 1}
    bag = Bag(initial)
    # __repr__ contains counts and total
    rep = repr(bag)
    assert "counts" in rep and "total=4" in rep
    # counts() matches initial
    cnt = bag.counts()
    assert cnt == initial
    # draw() returns all tokens and empties bag
    drawn = bag.draw()
    assert isinstance(drawn, list)
    assert len(drawn) == sum(initial.values())
    assert len(bag) == 0
    # drawn contains correct colors
    colors = [t.color for t in drawn]
    for color, num in initial.items():
        assert colors.count(color) == num
    # return_tokens restores tokens
    bag.return_tokens(drawn)
    assert bag.counts() == initial
    assert len(bag) == sum(initial.values())


def test_bag_from_json(tmp_path):
    # Create a JSON file
    data = {"black": 3, "red": 2}
    p = tmp_path / "tokens.json"
    p.write_text(json.dumps(data))
    bag = Bag.from_json(str(p))
    assert isinstance(bag, Bag)
    assert bag.counts() == data


def test_board_fill_and_eligible_draws_1():

    # Example usage
    initial_counts = {
        "black": 1,
        # "red": 4,
        # "blue": 4,
        # "green": 4,
        # "white": 4,
        # "pearl": 2,
        # "gold": 1,  # Wildcard tokens
    }
    bag = Bag(initial_counts)
    board = Board()
    tokens = bag.draw()
    board.fill_grid(tokens)
    eligible = board.eligible_draws()
    assert len(eligible) == 1
    assert board.grid[2][2].color == "black"

def test_board_fill_and_eligible_draws_2():
    # Example usage
    initial_counts = {
        "black": 1,
        "red": 1,
        "blue": 1,
        "green": 1,
        "white": 1,
        "pearl": 1,
        "gold": 1,  # Wildcard tokens
    }
    bag = Bag(initial_counts)
    board = Board()
    tokens = bag.draw(shuffle=False)  # Ensure predictable order
    board.fill_grid(tokens)
    eligible = board.eligible_draws()
    assert len(eligible) == 20  # Each color has one token
    assert board.grid[2][2].color == "black" # seed 42

def test_draw_until_empty():
    initial_counts = {
        "black": 4,
        "red": 4,
        "blue": 4,
        "green": 4,
        "white": 4,
        "pearl": 2,
        "gold": 2,  # Wildcard tokens
    }
    bag = Bag(initial_counts)
    board = Board()
    tokens = bag.draw(shuffle=False)  # Ensure predictable order
    board.fill_grid(tokens)
    eligible = board.eligible_draws()
    while len(eligible) > 0:
        # Draw all eligible tokens
        drawn = board.draw_tokens(eligible[0])
        # Check that the board is updated
        eligible = board.eligible_draws()
    assert len(eligible) == 0


def test_board_invalid_draw_raises():
    initial = {"green": 1}
    bag = Bag(initial)
    board = Board()
    tokens = bag.draw()
    board.fill_grid(tokens)
    # attempt to draw wrong location
    with pytest.raises(ValueError):
        board.draw_tokens({"green": [(0,1)]})
