import json
import itertools
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
from gymnasium import spaces

from actions import ActionType, Action
from cards import Deck, Card
from tokens import Bag
from desk import Board
from player import PlayerState
import yaml 


class SplendorDuelEnv(gym.Env):
    """
    Gymnasium-style environment for Splendor Duel.

    Observation:
        A dict encoding current board state, both players, and whose turn it is.
    Action Space:
        Discrete enumeration of all valid actions via ActionType and payload.
    Reward:
        +1 for winning on your turn, -1 for losing, 0 otherwise.
    """

    # metadata = {"render_modes": ["human", "ansi"], "render_fps": 4}

    def __init__(
        self,
        card_json: str = "data/cards.json",
        token_json: str = "data/tokens.json",
        initial_privileges: int = 3,
        royal_cards: Optional[List[Card]] = None,
        # render_mode: str = "human",
    ):
        # Load decks for levels 1-3
        decks: Dict[int, Deck] = {
            lvl: Deck.from_json(card_json, level=lvl) for lvl in [1, 2, 3]
        }
        # Load initial token counts from JSON
        with open(token_json, "r", encoding="utf-8") as f:
            initial_counts: Dict[str, int] = json.load(f)
        if royal_cards is None:
            royal_cards = []
        # Initialize board and players
        self.board = Board(decks, initial_counts, initial_privileges, royal_cards)
        self.players: List[PlayerState] = [PlayerState(), PlayerState()]
        self.current_player: int = 0
        self.done: bool = False
        self.winner: Optional[int] = None
        self.render_mode = render_mode

        # Placeholder action and observation spaces (refine later)
        self.action_space = spaces.Discrete(1)
        self.observation_space = spaces.Dict({})

    def reset(self) -> Tuple[Dict[str, Any], Dict]:
        """
        Reset the game to an initial state.

        Returns:
            observation (dict): Starting observation.
            info (dict): Optional info dict (empty).
        """
        # Reinitialize by calling __init__
        self.__init__()
        return self._get_observation(), {}

    def step(
        self, action: Action
    ) -> Tuple[Dict[str, Any], float, bool, bool, Dict[str, Any]]:
        """
        Apply an Action, advance game state, compute reward.

        Returns:
            observation, reward, terminated, truncated, info
        """
        if self.done:
            raise RuntimeError("Game is finished. Call reset() to start a new game.")
        player = self.players[self.current_player]
        # Handle action types
        if action.type == ActionType.TAKE_TOKENS:
            colors: List[str] = action.payload.get("colors", [])
            tokens = self.board.take_tokens(colors)
            player.add_tokens([t.color for t in tokens])
        elif action.type == ActionType.TAKE_GOLD_AND_RESERVE:
            # Take one gold (pearl)
            gold = self.board.take_tokens(["pearl"])
            player.add_tokens([t.color for t in gold])
            # Reserve card
            level = action.payload["level"]
            idx = action.payload["index"]
            card = self.board.reserve_card(level, idx)
            player.reserve_card(card)
        elif action.type == ActionType.PURCHASE_CARD:
            # Purchase reserved or board card
            if action.payload.get("reserved_index") is not None:
                idx = action.payload["reserved_index"]
                card = player.reserved.pop(idx)
            else:
                lvl = action.payload["level"]
                idx = action.payload["index"]
                card = self.board.purchase_card(lvl, idx)
            player.pay_for_card(card)
        elif action.type == ActionType.USE_PRIVILEGE:
            if self.board.use_privilege():
                colors = action.payload.get("colors", [])
                tokens = []
                for c in colors:
                    t = self.board.take_tokens([c])
                    if t:
                        tokens.append(t[0])
                player.add_tokens([t.color for t in tokens])
        # REPLENISH_BOARD: no-op (board auto-refills on reserve/purchase)

        # Check win condition
        reward = 0.0
        if player.has_won():
            self.done = True
            self.winner = self.current_player
            reward = 1.0
        # Switch turn
        self.current_player = 1 - self.current_player
        return self._get_observation(), reward, self.done, False, {}

    def _get_observation(self) -> Dict[str, Any]:
        """
        Internal helper to build current observation dict.
        """
        return {
            "board": {
                "tokens": self.board.tokens(),
                "privileges": self.board.privileges,
                "pyramid": {
                    lvl: [c.to_dict() if c else None for c in self.board.pyramid[lvl]]
                    for lvl in self.board.pyramid
                },
                "royals": [c.to_dict() for c in self.board.royal_cards],
            },
            "players": [
                {
                    "tokens": p.tokens,
                    "bonuses": p.bonuses,
                    "reserved": [c.to_dict() for c in p.reserved],
                    "purchased": [c.to_dict() for c in p.purchased],
                    "privileges": p.privileges,
                    "points": p.points,
                    "crowns": p.crowns,
                }
                for p in self.players
            ],
            "current_player": self.current_player,
        }

    def legal_actions(self) -> List[Action]:
        """
        Compute and return a list of valid Actions for the current player.
        """
        actions: List[Action] = []
        player = self.players[self.current_player]
        # TAKE_TOKENS: combinations of up to 3 distinct non-gold colors
        available = [
            c for c, cnt in self.board.tokens().items() if c != "pearl" and cnt > 0
        ]
        for r in [1, 2, 3]:
            for combo in itertools.combinations(available, r):
                actions.append(Action(ActionType.TAKE_TOKENS, {"colors": list(combo)}))
        # TAKE_GOLD_AND_RESERVE
        for lvl, slots in self.board.pyramid.items():
            for idx, card in enumerate(slots):
                if card:
                    actions.append(
                        Action(
                            ActionType.TAKE_GOLD_AND_RESERVE,
                            {"level": lvl, "index": idx},
                        )
                    )
        # PURCHASE_CARD from board
        for lvl, slots in self.board.pyramid.items():
            for idx, card in enumerate(slots):
                if card and player.can_afford(card):
                    actions.append(
                        Action(
                            ActionType.PURCHASE_CARD,
                            {"level": lvl, "index": idx},
                        )
                    )
        # PURCHASE_CARD from reserved
        for idx, card in enumerate(player.reserved):
            if player.can_afford(card):
                actions.append(
                    Action(
                        ActionType.PURCHASE_CARD,
                        {"reserved_index": idx},
                    )
                )
        # USE_PRIVILEGE
        if self.board.privileges > 0:
            # we leave payload empty for agent to fill colors
            actions.append(Action(ActionType.USE_PRIVILEGE, {}))
        # Always allow replenishing the board when no mandatory actions available
        actions.append(Action(ActionType.REPLENISH_BOARD, {}))
        return actions

    def render(self, mode: str = "human") -> Optional[str]:
        """
        Render the current state. For 'human', print to stdout; for 'ansi', return a string.
        """
        obs = self._get_observation()
        # Minimal rendering: current player and scores
        text = (
            f"Player 1 pts={self.players[0].points}  |  "
            f"Player 2 pts={self.players[1].points}\n"
            f"It's Player {self.current_player+1}\n"
        )
        if mode == "human":
            print(text)
            return None
        return text

if __name__ == "__main__":
    
    with open("./data/box.yaml", "r", encoding="utf-8") as f:
        box = yaml.safe_load(f)
    env = SplendorDuelEnv(
        card_json=box["cards"],
        token_json=box["tokens"],
        initial_privileges=box["privileges"],
        royal_cards=box.get("royals", []),
    )
