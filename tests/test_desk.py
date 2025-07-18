import json
import pytest
from model.desk import Desk
from model.actions import ActionType
from model.tokens import Token

def make_cards_json(path):
    # Create a minimal cards.json with exactly required counts
    # level_1: 5 cards, level_2: 4, level_3: 3
    data = {}
    for lvl, count in [(1,5), (2,4), (3,3)]:
        key = f"level_{lvl}"
        data[key] = [
            {
                "id": f"{lvl}-{i+1:02d}",
                "level": lvl,
                "color": "Black",
                "points": 0,
                "bonus": 0,
                "ability": None,
                "crowns": 0,
                "cost": {"black":0,"red":0,"green":0,"blue":0,"white":0,"pearl":0}
            }
            for i in range(count)
        ]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def make_tokens_json(path):
    # Enough tokens to fill 5x5 grid
    counts = {"black":25}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(counts, f)


def make_royals_json(path):
    data = {"royals": [{"id":"R1","points":3,"ability":None} ]}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


@pytest.fixture
def setup_desk(tmp_path):
    cards_path = tmp_path / "cards.json"
    tokens_path = tmp_path / "tokens.json"
    royals_path = tmp_path / "royals.json"
    make_cards_json(cards_path)
    make_tokens_json(tokens_path)
    make_royals_json(royals_path)
    desk = Desk(
        card_json=str(cards_path),
        token_json=str(tokens_path),
        royal_json=str(royals_path),
        initial_privileges=2
    )
    return desk


def test_initial_state(setup_desk):
    desk = setup_desk
    # Current player index
    assert desk.current_player_index == 0
    # No winner yet
    assert not desk.is_game_over()
    assert desk.winner is None
    # Privileges set
    assert desk.privileges == 2
    # Pyramid slot counts
    assert len(desk.pyramid.slots[1]) == 5
    assert len(desk.pyramid.slots[2]) == 4
    assert len(desk.pyramid.slots[3]) == 3
    # Board has 0 tokens and bag has 25
    board_counts = desk.board.counts()
    assert sum(board_counts.values()) == 0
    bag_counts = desk.bag.counts()
    assert sum(bag_counts.values()) == 25


def test_use_privilege_and_replenish_action(setup_desk):
    desk = setup_desk
    player = desk.current_player
    # Player has no privileges yet
    assert player.privileges == 0
    acts = desk.legal_actions()
    use_priv = [a for a in acts if a.type == ActionType.USE_PRIVILEGE]
    # no USE_PRIVILEGE actions available because no privileges
    assert not use_priv, "No USE_PRIVILEGE actions available"

    # Replenish board, after the board should be filled with tokens
    replenish_actions = [a for a in acts if a.type == ActionType.REPLENISH_BOARD]
    assert replenish_actions, "REPLENISH_BOARD actions should be available"
    desk.apply_action(replenish_actions[0])
    # After replenishing, board should have 25 black tokens
    board_counts = desk.board.counts()
    assert board_counts.get(Token("black"), 0) == 25, "Board should have 25 black tokens after replenishing"

    # Add a privilege to the player
    player.privileges += 1
    acts = desk.legal_actions()
    use_priv = [a for a in acts if a.type == ActionType.USE_PRIVILEGE]
    # Now USE_PRIVILEGE action should be available
    assert use_priv, "USE_PRIVILEGE action should be available after adding privilege"

    action = use_priv[0]
    desk.apply_action(action)
    
    board_counts = desk.board.counts()
    assert sum(board_counts.values()) < 25, "Board should have less than 25 tokens after using privilege"


def test_take_tokens_action(setup_desk):
    desk = setup_desk
    player = desk.current_player
    # legal actions include TAKE_TOKENS
    actions = desk.legal_actions()

    # Check if TAKE_TOKENS action is available
    take_token_actions = [a for a in actions if a.type == ActionType.TAKE_TOKENS]
    assert not take_token_actions, "Board empty - no TAKE_TOKENS actions should be available"

    # check if PURCHASE_CARD is available
    purchase_card_actions = [a for a in actions if a.type == ActionType.PURCHASE_CARD]
    assert purchase_card_actions, "PURCHASE_CARD actions should be available"

    # Check if USE_PRIVILEGE is available
    replenish_actions = [a for a in actions if a.type == ActionType.REPLENISH_BOARD]
    assert replenish_actions, "REPLENISH_BOARD actions should be available"
    
    # Replenish board, after the board should be filled with tokens
    desk.apply_action(replenish_actions[0])
    assert desk.board.counts() == {Token("black"): 25}, "Board should have 25 black tokens after replenishing"

    actions = desk.legal_actions()
    take_token_actions = [a for a in actions if a.type == ActionType.TAKE_TOKENS]
    assert take_token_actions, "After replenishing, TAKE_TOKENS actions should be available"

    desk.apply_action(take_token_actions[0])
    assert desk.board.counts().get(Token("black"), 0) < 25, "Board should have less than 25 black tokens after taking tokens"
    
    # tokens added to player
    sum_tokens = 0
    sum_tokens += desk.players[0].tokens[Token("black")]
    sum_tokens += desk.players[1].tokens[Token("black")]
    assert sum_tokens > 0, "Player should have black tokens after taking"

    # assert drawn equal to taken
    assert desk.board.counts().get(Token("black"), 0) == 25 - sum_tokens, \
        "Bag should have remaining black tokens after taking"
    


def test_purchase_card_action(setup_desk):
    desk = setup_desk
    # Ensure first player can afford any card (cost zero)
    acts = desk.legal_actions()
    pur_actions = [a for a in acts if a.type == ActionType.PURCHASE_CARD]
    assert pur_actions, "No PURCHASE_CARD actions available"
    action = pur_actions[0]
    player = desk.current_player
    # no purchased yet
    assert len(player.purchased) == 0
    desk.apply_action(action)
    # purchased increased
    assert len(player.purchased) == 1
    # turn switched
    assert desk.current_player_index == 1
