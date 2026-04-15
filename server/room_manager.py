"""
RoomManager: global registry of active game rooms.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from fastapi import WebSocket

from server.game_room import GameRoom


_ROOM_ID_CHARS = string.ascii_uppercase + string.digits
_ROOM_ID_LEN = 6
_ROOM_TTL_HOURS = 1


class RoomManager:
    """
    Thread-safe (asyncio single-thread) registry of GameRoom instances.
    """

    def __init__(self, card_json: str, token_json: str, royal_json: str, initial_privileges: int = 3):
        self._rooms: Dict[str, GameRoom] = {}
        self.card_json = card_json
        self.token_json = token_json
        self.royal_json = royal_json
        self.initial_privileges = initial_privileges

    # ------------------------------------------------------------------
    # Room lifecycle
    # ------------------------------------------------------------------

    def create_room(self) -> str:
        """Create a new room and return its ID."""
        room_id = self._generate_id()
        self._rooms[room_id] = GameRoom(
            room_id,
            self.card_json,
            self.token_json,
            self.royal_json,
            self.initial_privileges,
        )
        return room_id

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self._rooms.get(room_id.upper())

    def join_room(
        self, room_id: str, player_name: str, ws: WebSocket
    ) -> Tuple[Optional[GameRoom], Optional[int], Optional[str]]:
        """
        Add a player to a room.

        Returns:
            (room, player_index, error_message)
            On success: (room, 0 or 1, None)
            On failure: (None, None, reason_string)
        """
        room = self.get_room(room_id)
        if room is None:
            return None, None, f"Room '{room_id}' not found"
        if room.is_full():
            return None, None, "Room is full"

        player_index = room.next_player_index()
        room.add_player(player_index, player_name, ws)
        return room, player_index, None

    def cleanup_stale_rooms(self) -> int:
        """Remove rooms inactive for more than TTL. Returns count removed."""
        cutoff = datetime.utcnow() - timedelta(hours=_ROOM_TTL_HOURS)
        stale = [rid for rid, room in self._rooms.items() if room.last_activity < cutoff]
        for rid in stale:
            del self._rooms[rid]
        return len(stale)

    def room_status(self, room_id: str) -> Optional[Dict]:
        room = self.get_room(room_id)
        if room is None:
            return None
        return {
            "room_id": room.room_id,
            "player_count": len(room.player_names),
            "game_started": room.game_started,
            "players": list(room.player_names.values()),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_id(self) -> str:
        for _ in range(20):  # avoid (unlikely) collision
            candidate = "".join(random.choices(_ROOM_ID_CHARS, k=_ROOM_ID_LEN))
            if candidate not in self._rooms:
                return candidate
        raise RuntimeError("Could not generate unique room ID")
