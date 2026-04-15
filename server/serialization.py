"""
Build the full game state snapshot sent to clients after every state change.
"""
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from server.game_room import GameRoom


def build_state_snapshot(room: "GameRoom", message: str = "") -> Dict[str, Any]:
    """
    Serialize the full game state into a JSON-ready dict for broadcast.

    Sent to both clients after every action, so they can re-render from scratch.
    """
    from model.game_state_machine import GameStateManager

    current_action = GameStateManager.get_current_action(room.session_state, room.desk)

    buttons = [
        {"text": btn.text, "action": btn.action, "enabled": btn.enabled}
        for btn in current_action.buttons
    ]

    return {
        "type": "game_state",
        "desk": room.desk.to_dict(),
        "session": room.session_state.to_dict(),
        "buttons": buttons,
        "explanation": current_action.explanation,
        "active_player_index": room.desk.current_player_index,
        "message": message,
        "message_history": room.message_history[-20:],  # last 20 messages
    }
