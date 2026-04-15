"""
GameRoom: owns one Desk instance, both player WebSocket connections,
and session state. Mirrors the GameController pattern but for async WebSockets.
"""
import copy
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

from model.desk import Desk
from model.player import PlayerState
from model.game_state_machine import GameState, GameSessionState, GameStateManager
from model.element_reference import ElementReference
from model.tokens import Token
from model.cards import Card, Deck
from model.actions import ActionButton


class BonusColor:
    """Thin wrapper used when a player clicks a color swatch (for joker assignment)."""
    def __init__(self, color: str):
        self.color = color


class GameRoom:
    """
    Owns all server-side state for one two-player game.

    Lifecycle:
      1. Created by RoomManager when the first player creates a room.
      2. Second player joins — game_started becomes True, board is filled.
      3. WebSocket handler drives state transitions via handle_select / handle_button.
      4. broadcast_state() pushes the full snapshot to both clients.
    """

    def __init__(self, room_id: str, card_json: str, token_json: str, royal_json: str, initial_privileges: int = 3):
        self.room_id = room_id
        self.desk = Desk(card_json, token_json, royal_json, initial_privileges)
        self.desk_snapshot: Optional[Desk] = None
        self.session_state = GameSessionState(
            current_state=GameState.START_OF_ROUND,
            current_selection=[],
        )
        self.message_history: List[str] = ["Welcome to Splendor Duel!"]
        # player_index (0 or 1) → WebSocket
        self.connections: Dict[int, WebSocket] = {}
        # player_index → player name
        self.player_names: Dict[int, str] = {}
        self.game_started: bool = False
        self.last_activity: datetime = datetime.utcnow()

    # ------------------------------------------------------------------
    # Player management
    # ------------------------------------------------------------------

    def add_player(self, player_index: int, name: str, ws: WebSocket) -> None:
        self.connections[player_index] = ws
        self.player_names[player_index] = name

    def next_player_index(self) -> int:
        """Return the index for the next player to join (0 or 1)."""
        return len(self.player_names)

    def is_full(self) -> bool:
        return len(self.player_names) >= 2

    def start_game(self) -> None:
        """Called once both players have connected."""
        player1 = PlayerState(self.player_names[0])
        player2 = PlayerState(self.player_names[1])
        self.desk.add_player(player1, player2)
        self.desk.board.fill_grid(self.desk.bag.draw())
        self.desk_snapshot = copy.deepcopy(self.desk)
        self.game_started = True
        self.message_history.append(
            f"Game started: {self.player_names[0]} vs {self.player_names[1]}"
        )

    # ------------------------------------------------------------------
    # Action handling (mirrors GameController logic)
    # ------------------------------------------------------------------

    def add_message(self, msg: str) -> None:
        if msg:
            self.message_history.append(msg)
            self.last_activity = datetime.utcnow()

    def handle_select(self, element_ref: ElementReference) -> str:
        """Process an element selection. Returns message string."""
        new_session, _success, message = GameStateManager.select_element(
            self.session_state, element_ref, self.desk, element_ref.element_type
        )
        self.session_state = new_session
        self.add_message(message)
        return message

    def handle_button(self, button: ActionButton) -> str:
        """Process a button click. Returns message string."""
        new_session, action, message = GameStateManager.handle_button_click(
            self.session_state, button, self.desk
        )
        self.session_state = new_session

        # Controller-level side effects (rollback / snapshot)
        if button.action == "rollback_to_start" and self.desk_snapshot is not None:
            self.desk = copy.deepcopy(self.desk_snapshot)
            message = "Rolled back to start of round"
        elif button.action == "finish_round":
            self.desk_snapshot = copy.deepcopy(self.desk)
            message = "Round finished - next player's turn"

        if action is not None:
            self.desk.apply_action(action)
            self.add_message(f"Action executed: {action.type.name}")

        self.add_message(message)
        return message

    # ------------------------------------------------------------------
    # WebSocket broadcast
    # ------------------------------------------------------------------

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        """Send JSON payload to all connected clients."""
        import json
        for ws in self.connections.values():
            try:
                await ws.send_json(payload)
            except Exception:
                pass  # disconnected client; handled elsewhere

    async def broadcast_state(self, message: str = "") -> None:
        """Build full state snapshot and broadcast to all clients."""
        from server.serialization import build_state_snapshot
        snapshot = build_state_snapshot(self, message)
        await self.broadcast(snapshot)

    async def send_to(self, player_index: int, payload: Dict[str, Any]) -> None:
        """Send JSON payload to a specific player."""
        ws = self.connections.get(player_index)
        if ws:
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # ElementReference reconstruction from wire data
    # ------------------------------------------------------------------

    def rebuild_element_ref(
        self,
        element_type: str,
        metadata: Dict[str, Any],
        player_index: int,
    ) -> Optional[ElementReference]:
        """
        Reconstruct a live ElementReference from the wire message.

        The client sends element_type + metadata; we look up the actual
        model object from the current desk state.
        """
        name_parts = [element_type]

        if element_type == "Token":
            pos = metadata.get("position")
            if pos is None:
                return None
            r, c = int(pos[0]), int(pos[1])
            token = self.desk.board.grid[r][c]
            if token is None:
                return None
            name = f"token_board_{r}_{c}"
            return ElementReference(
                name=name,
                element=token,
                element_type="Token",
                metadata={"position": (r, c), "source": "board"},
            )

        elif element_type == "Card":
            if "reserved_index" in metadata:
                idx = int(metadata["reserved_index"])
                player = self.desk.players[player_index]
                if idx >= len(player.reserved):
                    return None
                card = player.reserved[idx]
                return ElementReference(
                    name=f"card_reserved_{player_index}_{idx}",
                    element=card,
                    element_type="Card",
                    metadata={"index": idx, "player": self.desk.players[player_index].name},
                )
            elif "level" in metadata and "index" in metadata:
                level = int(metadata["level"])
                idx = int(metadata["index"])
                card = self.desk.pyramid.slots.get(level, [])[idx] if level in self.desk.pyramid.slots else None
                if card is None:
                    return None
                return ElementReference(
                    name=f"card_L{level}_slot{idx}",
                    element=card,
                    element_type="Card",
                    metadata={"level": level, "index": idx},
                )
            return None

        elif element_type == "Deck":
            level = int(metadata.get("level", 0))
            deck = self.desk.pyramid.decks.get(level)
            if deck is None:
                return None
            return ElementReference(
                name=f"deck_L{level}",
                element=deck,
                element_type="Deck",
                metadata={"level": level},
            )

        elif element_type == "Royal":
            idx = int(metadata.get("index", -1))
            royal = self.desk.royals.get(idx)
            if royal is None:
                return None
            return ElementReference(
                name=f"royal_{idx}",
                element=royal,
                element_type="Royal",
                metadata={"index": idx},
            )

        elif element_type == "BonusColor":
            color = metadata.get("color", "")
            return ElementReference(
                name=f"bonus_color_{color}",
                element=BonusColor(color),
                element_type="BonusColor",
                metadata={"color": color, "player": self.desk.players[player_index].name},
            )

        return None
