# Splendor Duel

A Python implementation of the board game **Splendor Duel** with a Pygame GUI.

## Quick Start

### Prerequisites

- Python 3.12+
- Required packages:
  - `pygame` - Game rendering
  - `pyyaml` - Configuration loading
  - `gymnasium` - (Optional) For AI/RL environment
  - `pytest` - For running tests

### Installation

```bash
# Install dependencies
pip install pygame pyyaml pytest

# (Optional) For the RL environment
pip install gymnasium
```

### Running the Game

```bash
# From the project root directory
python controller/game_controller.py
python -m controller.game_controller
```

Or run directly:

```bash
python -c "
from controller.game_controller import GameController
from model.player import PlayerState
import yaml

with open('data/box.yaml', 'r') as f:
    cfg = yaml.safe_load(f)

ctrl = GameController(
    card_json=cfg['cards'],
    token_json=cfg['tokens'],
    royal_json=cfg['royals'],
    initial_privileges=cfg.get('privileges', 3),
    asset_path='data/images'
)

player1 = PlayerState('Player 1')
player1.privileges = 3
player2 = PlayerState('Player 2')
ctrl.desk.add_player(player1, player2)
ctrl.desk.board.fill_grid(ctrl.desk.bag.draw())

ctrl.run()
"
```

### Running Tests

```bash
pytest -v
```

---

## Project Architecture

```
SplendorDuel/
├── controller/           # Game logic orchestration
│   ├── game_controller.py   # Main Pygame loop, input handling
│   └── selection_manager.py # Element selection logic
│
├── model/                # Core game data models
│   ├── actions.py           # ActionType enum, Action class
│   ├── cards.py             # Card, Deck, Pyramid, Royal classes
│   ├── desk.py              # Desk (game engine) - manages all game state
│   ├── game_state_machine.py # GameState enum, state transitions
│   ├── player.py            # PlayerState class
│   ├── tokens.py            # Token, Bag, Board classes
│   └── piece.py             # Base class for game pieces
│
├── view/                 # Rendering and UI
│   ├── assets.py            # AssetManager for loading images
│   ├── game_view.py         # GameView - all Pygame rendering
│   └── layout.py            # LayoutRegistry, HSplit, VSplit helpers
│
├── data/                 # Game data files
│   ├── box.yaml             # Configuration file
│   ├── cards.json           # Card definitions
│   ├── tokens.json          # Token counts
│   ├── royals.json          # Royal card definitions
│   └── images/              # Game assets (sprites, backgrounds)
│
├── tests/                # Unit tests (pytest)
├── support/              # Documentation and rules
├── scripts/              # Utility scripts
├── env.py                # Gymnasium environment (WIP)
└── overall.py            # Entry point imports
```

---

## Game Flow (State Machine)

The game follows a state machine defined in `model/game_state_machine.py`:

```
START_OF_ROUND
    ├── USE_PRIVILEGE (optional) → back to START_OF_ROUND
    ├── REPLENISH_BOARD (optional) → CHOOSE_MANDATORY_ACTION
    └── [Mandatory Actions]:
        ├── PURCHASE_CARD → POST_ACTION_CHECKS
        ├── TAKE_TOKENS → POST_ACTION_CHECKS
        └── TAKE_GOLD_AND_RESERVE → POST_ACTION_CHECKS

POST_ACTION_CHECKS
    └── CONFIRM_ROUND → START_OF_ROUND (next player)
```

See `support/state_changing.md` for detailed state transitions.

---

## Current Development Status

### ✅ Completed Features

| Feature | Status |
|---------|--------|
| Core game model (Cards, Tokens, Players) | ✅ Done |
| Pygame GUI with full layout | ✅ Done |
| State machine for game flow | ✅ Done |
| START_OF_ROUND state | ✅ Done |
| USE_PRIVILEGE action | ✅ Done |
| REPLENISH_BOARD action | ✅ Done |
| CHOOSE_MANDATORY_ACTION state | ✅ Done |
| PURCHASE_CARD action | ✅ Done |
| TAKE_TOKENS action | ✅ Done |
| TAKE_GOLD_AND_RESERVE action | ✅ Done |
| POST_ACTION_CHECKS state | ✅ Done |
| DISCARD_TOKENS state | ✅ Done |
| CONFIRM_ROUND state | ✅ Done |
| Unit tests (52 passing) | ✅ Done |

### 🚧 TODO - Remaining Features

| Feature | Location | Notes |
|---------|----------|-------|
| ROYAL_SELECTION state | `game_state_machine.py:33` | When player qualifies for a royal |
| Card Abilities - 2nd Turn | `game_state_machine.py:34` | Cards that grant extra turns |
| Card Abilities - Joker | `game_state_machine.py:35` | Wild color bonus |
| Card Abilities - 2nd Color | `game_state_machine.py:36` | Cards with dual color bonus |
| Card Abilities - Privilege | `game_state_machine.py:37` | Cards that grant privileges |
| Card Abilities - Steal | `game_state_machine.py:38` | Steal from opponent |
| Victory condition handling | `desk.py:194` | Check win in controller |
| Replenish/Reserve no-rollback | `game_state_machine.py:20` | Prevent rollback after certain actions |
| Face-down deck reservations | `cards.py:205` | Reserve from top of deck |

### 🔮 Future Enhancements

- [ ] AI opponent (Gymnasium environment in `env.py`)
- [ ] Network multiplayer
- [ ] Save/Load game state
- [ ] Sound effects
- [ ] Animations

---

## Key Classes

### `Desk` (model/desk.py)
The main game engine that holds all game state:
- `pyramid` - Card pyramid (3 levels)
- `board` - 5x5 token grid
- `bag` - Token bag for refilling
- `players` - Two PlayerState objects
- `royals` - Available royal cards
- `privileges` - Scroll tokens on the table

### `GameStateManager` (model/game_state_machine.py)
Stateless functions for game state transitions:
- `handle_button_click()` - Process UI button actions
- `select_element()` - Handle element selection
- `get_current_action()` - Get available actions for current state

### `GameController` (controller/game_controller.py)
Orchestrates the Pygame loop:
- Handles user input (clicks, keyboard)
- Manages `GameSessionState` (current state + selection)
- Calls `GameStateManager` for state transitions
- Triggers `GameView` rendering

### `GameView` (view/game_view.py)
All Pygame rendering:
- Main panel (board, pyramid, royals, bag)
- Player panels (tokens, cards, reserved)
- Action panel (buttons for current state)
- Uses `LayoutRegistry` for click detection

---

## Controls

- **Left Click** - Select tokens, cards, or action buttons
- **ESC / Q** - Quit game

---

## Development Notes

### Adding a New State

1. Add the state to `GameState` enum in `game_state_machine.py`
2. Add selection rules in `GameStateConfig.SELECTION_RULES`
3. Create handler method `_handle_<state>_buttons()`
4. Add case to `handle_button_click()` match statement
5. Add case to `get_current_action()` for UI buttons
6. Write tests in `tests/test_game_state_machine.py`

### Testing

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_game_state_machine.py -v

# Run with coverage (if installed)
pytest --cov=model --cov=controller --cov=view
```

---

## License

This is a personal project implementing the Splendor Duel board game for learning purposes.

