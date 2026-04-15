"""
FastAPI entry point for Splendor Duel multiplayer server.

Routes:
  POST /create-room              → {"room_id": "ABC123"}
  GET  /room/{room_id}/status    → room info dict
  GET  /                         → frontend index.html (once frontend exists)
  GET  /assets/{path}            → data/images/* static files
  WS   /ws/{room_id}/{player_name}
"""
import asyncio
import os
import yaml
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from model.actions import ActionButton
from server.room_manager import RoomManager


# ------------------------------------------------------------------
# Load config once at startup
# ------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(_BASE_DIR, "data", "box.yaml"), "r", encoding="utf-8") as _f:
    _cfg = yaml.safe_load(_f)

room_manager = RoomManager(
    card_json=_cfg["cards"],
    token_json=_cfg["tokens"],
    royal_json=_cfg["royals"],
    initial_privileges=_cfg.get("privileges", 3),
)


# ------------------------------------------------------------------
# Background cleanup task
# ------------------------------------------------------------------
async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(3600)  # every hour
        removed = room_manager.cleanup_stale_rooms()
        if removed:
            print(f"[cleanup] Removed {removed} stale room(s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------
app = FastAPI(title="Splendor Duel", lifespan=lifespan)

# Serve card/token images from data/images/
_images_dir = os.path.join(_BASE_DIR, "data", "images")
if os.path.isdir(_images_dir):
    app.mount("/assets", StaticFiles(directory=_images_dir), name="assets")

_frontend_dir = os.path.join(_BASE_DIR, "frontend", "dist")


# ------------------------------------------------------------------
# HTTP routes
# ------------------------------------------------------------------
@app.post("/create-room")
async def create_room() -> Dict[str, str]:
    room_id = room_manager.create_room()
    return {"room_id": room_id}


@app.get("/room/{room_id}/status")
async def room_status(room_id: str) -> Dict[str, Any]:
    status = room_manager.room_status(room_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return status


@app.get("/")
async def serve_frontend():
    index = os.path.join(_frontend_dir, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse({"message": "Frontend not built yet. Run: cd frontend && npm run build"})


# ------------------------------------------------------------------
# WebSocket handler
# ------------------------------------------------------------------
@app.websocket("/ws/{room_id}/{player_name}")
async def websocket_endpoint(ws: WebSocket, room_id: str, player_name: str):
    await ws.accept()

    room, player_index, error = room_manager.join_room(room_id, player_name, ws)
    if error:
        await ws.send_json({"type": "error", "message": error})
        await ws.close()
        return

    # Notify this player they joined
    await ws.send_json({
        "type": "room_joined",
        "player_index": player_index,
        "room_id": room_id,
        "player_name": player_name,
    })

    # If room is now full, start the game
    if room.is_full():
        room.start_game()
        await room.broadcast({"type": "game_start", "players": list(room.player_names.values())})
        await room.broadcast_state("Game started!")
    else:
        await ws.send_json({"type": "waiting", "message": "Waiting for opponent..."})

    try:
        while True:
            data: Dict[str, Any] = await ws.receive_json()
            await _handle_message(room, player_index, data)
    except WebSocketDisconnect:
        del room.connections[player_index]
        # Notify remaining player
        await room.broadcast({
            "type": "player_disconnected",
            "player_index": player_index,
            "message": f"{player_name} disconnected",
        })


async def _handle_message(room, player_index: int, data: Dict[str, Any]) -> None:
    """Dispatch an incoming WebSocket message from one player."""
    msg_type = data.get("type")

    # Enforce turn order for game actions
    if msg_type in ("select_element", "button_click"):
        if not room.game_started:
            await room.send_to(player_index, {"type": "error", "message": "Game not started yet"})
            return
        if player_index != room.desk.current_player_index:
            await room.send_to(player_index, {"type": "error", "message": "Not your turn"})
            return

    if msg_type == "select_element":
        element_type = data.get("element_type", "")
        metadata = data.get("metadata", {})

        element_ref = room.rebuild_element_ref(element_type, metadata, player_index)
        if element_ref is None:
            await room.send_to(player_index, {
                "type": "error",
                "message": f"Could not resolve element: type={element_type} metadata={metadata}",
            })
            return

        message = room.handle_select(element_ref)
        await room.broadcast_state(message)

    elif msg_type == "button_click":
        action_str = data.get("action", "")
        # Find the matching button from the current action
        from model.game_state_machine import GameStateManager
        current_action = GameStateManager.get_current_action(room.session_state, room.desk)
        button = next((b for b in current_action.buttons if b.action == action_str), None)
        if button is None:
            # Button not in current action — still create it (state machine validates)
            button = ActionButton(text=action_str, action=action_str, enabled=True)

        message = room.handle_button(button)
        await room.broadcast_state(message)

    else:
        await room.send_to(player_index, {"type": "error", "message": f"Unknown message type: {msg_type}"})
