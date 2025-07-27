import json
import yaml
import sys
import os
from typing import Any, Dict, List, Optional, Tuple

# Import from model directory (same directory)
from model.cards import Deck, Pyramid, Royal, Card
from model.tokens import Bag, Board, Token
from model.player import PlayerState
from model.actions import ActionType, Action, ActionButton
from model.game_state_machine import GameState, CurrentAction


class Desk:
    """
    Core game engine ("desk") for Splendor Duel.
    Manages the shared pyramid, token board, royal pool, players, privileges, and turn logic.
    """

    def __init__(
        self,
        card_json: str,
        token_json: str,
        royal_json: str,
        initial_privileges: int = 3,
    ):
        # Load decks for levels 1, 2, 3
        decks: Dict[int, Deck] = {
            level: Deck.from_json(card_json, level=level) for level in (1, 2, 3)
        }
        # Pyramid layout of cards
        self.pyramid = Pyramid(decks)
        # Token board (5×5 grid)
        with open(token_json, "r", encoding="utf-8") as f:
            counts: Dict[str, int] = json.load(f)
        tokens = {Token(color): count for color, count in counts.items()}
        self.bag = Bag(tokens)
        self.board = Board()
        # self.board.fill_grid(self.bag.draw())
        # Royal cards pool
        self.royals: List[Royal] = Royal.from_json(royal_json)
        # Privileges (scrolls) pool above board
        self.privileges: int = initial_privileges
        # Two-player states

        self.players: List[PlayerState] = []
        # Index of current player (0 or 1)
        self.current_player_index: int = 0
        # Winner index when game ends
        self.winner: Optional[int] = None

    @property
    def current_player(self) -> PlayerState:
        return self.players[self.current_player_index]
    
    def add_player(self, player1: PlayerState, player2: PlayerState):
        self.players.append(player1)
        self.players.append(player2)

    def next_player(self) -> None:
        """
        Advance turn to the other player.
        """
        self.current_player_index = 1 - self.current_player_index

    def legal_take_tokens(self) -> List[Action]:
        actions: List[Action] = []
        for combo in self.board.eligible_draws():
            actions.append(Action(ActionType.TAKE_TOKENS, {"combo": combo}))
        return actions

    def legal_actions(self) -> List[Action]:
        """
        Compute all legal game moves for the current player.

        Returns:
            List[Action]: Possible actions to choose from.
        """
        actions: List[Action] = []
        player = self.current_player

        # 1) Option move one: USE_PRIVILEGE: spend x scroll to draw x tokens
        if player.privileges > 0:
            for token, positions in self.board.privileges_draws().items():
                for position in positions:
                    actions.append(Action(ActionType.USE_PRIVILEGE, {"token": token, "position": position}))

        # 2) Option move two: REPLENISH_BOARD: refill board tokens or cards
        if not self.bag.is_empty():
            actions.append(Action(ActionType.REPLENISH_BOARD, {}))

        # 1) TAKE_TOKENS: any eligible 1-3 gem/pearl or single gold line
        for combo in self.board.eligible_draws():
            actions.append(Action(ActionType.TAKE_TOKENS, {"combo": combo}))

        # 2) TAKE_GOLD_AND_RESERVE: reserve any pyramid card + take one gold token
        if self.board.counts().get("gold", 0) > 0 and len(player.reserved) < 3:
            # for every gold token available
            for color, positions in self.board.eligible_draws().items():
                if color == "gold":
                    for level, slots in self.pyramid.slots.items():
                        for idx, card in enumerate(slots):
                            if card:
                                actions.append(
                                    Action(
                                        ActionType.TAKE_GOLD_AND_RESERVE,
                                        {
                                            "gold_token_positions": positions,
                                            "level": level,
                                            "index": idx,
                                        },
                                    )
                                )

        # 3) PURCHASE_CARD: from pyramid if affordable
        for level, slots in self.pyramid.slots.items():
            for idx, card in enumerate(slots):
                if card and player.can_afford(card):
                    actions.append(
                        Action(
                            ActionType.PURCHASE_CARD,
                            {"level": level, "index": idx},
                        )
                    )
        # 4) PURCHASE_CARD: from reserved
        for idx, card in enumerate(player.reserved):
            if player.can_afford(card):
                actions.append(
                    Action(
                        ActionType.PURCHASE_CARD,
                        {"reserved_index": idx},
                    )
                )

        return actions

    def apply_action(self, action: Action) -> None:
        """
        Execute the given action, updating game state.

        Args:
            action (Action): Selected action to perform.
        """
        player = self.current_player

        match action.type:
            case ActionType.USE_PRIVILEGE:
                player.use_privilege()
                player.add_tokens(self.board.draw_tokens({action.payload["token"]: [action.payload["position"]]}))

            case ActionType.REPLENISH_BOARD:
                self.board.fill_grid(self.bag.draw())
                # Give the other player a privilege
                other_player = self.players[1 - self.current_player_index]
                if self.privileges > 0:
                    other_player.add_privilege()
                    self.privileges -= 1
                else:
                    # If no privileges left, take one from current player
                    other_player.add_privilege()
                    player.privileges -= 1

            case ActionType.TAKE_TOKENS:
                player.add_tokens(self.board.draw_tokens(action.payload["combo"]))

            case ActionType.TAKE_GOLD_AND_RESERVE:
                gold_token, gold_token_positions, card, level, idx = (
                    action.payload["gold_token"],
                    action.payload["gold_token_positions"],
                    action.payload["card"],
                    action.payload["card_level"],
                    action.payload["card_index"],
                )

                player.add_tokens(self.board.draw_gold({Token("gold"): [gold_token_positions]}))
                if action.payload["card_index"] == 0:
                    player.reserve_card(card)
                else:
                    player.reserve_card(self.pyramid.get_card(level, idx))
                    self.pyramid.fill_card(level, idx)

            case ActionType.PURCHASE_CARD:
                if "reserved_index" in action.payload:
                    idx = action.payload["reserved_index"]
                    card = player.reserved.pop(idx)
                else:
                    level, idx = action.payload["level"], action.payload["index"]
                    card = self.pyramid.get_card(level, idx)
                    self.pyramid.fill_card(level, idx)

                player.pay_for_card(card, self.bag)

        # TODO: handle victory and turn advance in the controller
        # # After any action, check victory
        # if player.has_won():
        #     self.winner = self.current_player_index

        # # Advance turn
        # self.next_player()

    def is_game_over(self) -> bool:
        """
        Check whether the game has finished.

        Returns:
            bool: True if a winner has been decided.
        """
        return self.winner is not None

    def __repr__(self) -> str:
        return (
            f"<Desk current_player={self.current_player_index} "
            f"players={[p.points for p in self.players]} "
            f"privileges={self.privileges} royals={len(self.royals)} "
            f"\n{self.pyramid} \n{self.board} "
            f"\nwinner={self.winner}>"
        )


if __name__ == "__main__":

    # load your box.yaml to get the paths
    with open("data/box.yaml", "r", encoding="utf-8") as f:
        box = yaml.safe_load(f)

    # now initialize
    desk = Desk(
        card_json=box["cards"],  # e.g. "data/cards.json"
        token_json=box["tokens"],  # e.g. "data/tokens.json"
        royal_json=box["royals"],  # e.g. "data/royals.json"
        initial_privileges=box.get("privileges", 3),
    )

    print(desk)
