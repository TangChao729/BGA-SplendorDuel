# Splendor Duel

A Python implementation of the board game **Splendor Duel** with a Pygame GUI.

## 📊 Project Status Summary

**Last Updated:** January 2026

### What Works ✅
- **Complete game loop** with state machine (11 states implemented)
- **Full Pygame GUI** with clickable elements and visual feedback
- **All mandatory actions**: Purchase cards, take tokens, take gold & reserve
- **Optional actions**: Use privilege, replenish board
- **Post-action flow**: Discard tokens, royal selection, round confirmation
- **Card abilities**: TURN (extra turn), PRIVILEGE (gain scroll)
- **52 passing unit tests** covering core game logic
- **Rollback support** at end of round

### What's Missing 🚧
- **3 card abilities**: Joker (1 COLOR), Take Token (TAKE 2ND SAME), Steal
- **Victory detection** in game loop (logic exists but not enforced)
- **Rollback prevention** after certain committed actions
- **Face-down deck reservations** (UI doesn't allow clicking decks)

### Quick Assessment
**~85% complete** - Core game is fully playable, missing some card abilities and polish.
**Estimated time to finish:** 4-8 hours for remaining abilities + victory handling.

---

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
    ├── ROYAL_SELECTION (if qualified) → CHECK_DISCARD
    └── CHECK_DISCARD → [DISCARD_TOKENS or CONFIRM_ROUND]

DISCARD_TOKENS
    └── CHECK_DISCARD → [DISCARD_TOKENS again or CONFIRM_ROUND]

CONFIRM_ROUND
    └── START_OF_ROUND (next player)
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
| CHECK_DISCARD state | ✅ Done |
| DISCARD_TOKENS state | ✅ Done |
| ROYAL_SELECTION state | ✅ Done |
| CONFIRM_ROUND state | ✅ Done |
| Card Ability - TURN | ✅ Done |
| Card Ability - PRIVILEGE | ✅ Done |
| Unit tests (52 passing) | ✅ Done |
| Discard tokens state | ✅ Done |

### 🚧 TODO - Remaining Features

| Priority | Feature | Files to Modify | Estimated Time |
|----------|---------|-----------------|----------------|
| 🔴 High | **Joker Ability (1 COLOR)** | `game_state_machine.py` (add state)<br>`desk.py` (trigger state)<br>`player.py` (overlap logic) | 2-3 hours |
| 🔴 High | **Take Token Ability (TAKE 2ND SAME)** | `game_state_machine.py` (add state)<br>`desk.py` (trigger + execute) | 1 hour |
| 🔴 High | **Steal Ability** | `game_state_machine.py` (add state)<br>`desk.py` (trigger + execute) | 1 hour |
| 🟡 Medium | **Victory Condition Enforcement** | `game_controller.py` (check after confirm)<br>`game_view.py` (victory screen) | 1-2 hours |
| 🟡 Medium | **Rollback Prevention** | `game_state_machine.py` (add committed flag)<br>`desk.py` (track committed actions) | 1 hour |
| 🟢 Low | **Face-down Deck Reservations** | `game_view.py` (make decks clickable)<br>`game_state_machine.py` (handle deck selection) | 30 min |

**Total Estimated Time to Complete:** 6.5-9.5 hours

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

## Development Guide

### 🎯 Where to Continue Development

Based on the current state, here are the **next priority tasks**:

#### 1. **Card Abilities (High Priority)** 
The main gameplay loop is complete, but several card abilities need implementation:

- **"1 COLOR" (Joker)** - Most complex ability
  - When purchased, must overlap with an existing bonus card
  - Takes the color of the overlapped card
  - Location: `model/desk.py` line 243 (TODO comment)
  - Requires: New state `CARD_ABILITY_JOKER` for card selection UI
  
- **"TAKE 2ND SAME"** - Take token matching card color
  - After purchasing, take 1 token from board matching card's color
  - Requires: New state `CARD_ABILITY_2ND_COLOR` for token selection
  
- **"STEAL"** - Steal token from opponent
  - After purchasing, take 1 Gem/Pearl token from opponent
  - Requires: New state `CARD_ABILITY_STEAL` for token selection
  
- **"1 COLOR/TURN"** - Combo ability (Joker + Extra Turn)
  - Currently only grants extra turn (line 242 in `desk.py`)
  - Needs joker logic added

#### 2. **Victory Condition Handling (Medium Priority)**
- Currently checked in `player.py:has_won()` but not enforced in game loop
- Need to add victory check in `GameController` after `CONFIRM_ROUND`
- Display winner and end game gracefully
- Location: `controller/game_controller.py`

#### 3. **Rollback Prevention (Medium Priority)**
- After replenishing board or reserving face-down cards, prevent rollback
- Currently players can always rollback at `CONFIRM_ROUND`
- Add flag to track "committed" actions
- Location: `model/game_state_machine.py` line 20 (TODO comment)

#### 4. **Face-down Deck Reservations (Low Priority)**
- Currently can only reserve visible pyramid cards
- Should allow clicking on deck to reserve top card
- Location: UI needs to make decks clickable in `TAKE_GOLD_AND_RESERVE` state

### 📝 Development Workflow

#### Adding a New Card Ability

1. **Define the state** in `GameState` enum (`model/game_state_machine.py`)
2. **Add selection rules** in `GameStateConfig.SELECTION_RULES`
3. **Create handler** method `_handle_<ability>_buttons()` in `GameStateManager`
4. **Add button handling** in `handle_button_click()` match statement
5. **Add UI buttons** in `get_current_action()` 
6. **Trigger from purchase** in `desk.apply_action()` under `PURCHASE_CARD` case
7. **Write tests** in `tests/test_game_state_machine.py` and `tests/test_desk.py`

#### Adding a New State

1. Add the state to `GameState` enum in `game_state_machine.py`
2. Add selection rules in `GameStateConfig.SELECTION_RULES`
3. Create handler method `_handle_<state>_buttons()`
4. Add case to `handle_button_click()` match statement
5. Add case to `get_current_action()` for UI buttons
6. Write tests in `tests/test_game_state_machine.py`

### 🧪 Testing

```bash
# Run all tests (currently 52 passing)
pytest -v

# Run specific test file
pytest tests/test_game_state_machine.py -v

# Run with coverage (if installed)
pytest --cov=model --cov=controller --cov=view

# Run tests in watch mode (requires pytest-watch)
ptw
```

### 🐛 Debugging Tips

1. **Check message history** - Bottom of game window shows action log
2. **Print desk state** - Add `print(desk.to_dict())` in controller
3. **Inspect selection** - Check `session_state.current_selection` 
4. **Visual asset checker** - Run `tests/visual_asset_checker.py` to verify images load
5. **State transitions** - Refer to `support/state_changing.md` for flow diagram

### 📂 Key Files to Know

| File | Purpose | Lines |
|------|---------|-------|
| `model/desk.py` | Core game engine, action execution | 315 |
| `model/game_state_machine.py` | State management, UI logic | 736 |
| `controller/game_controller.py` | Pygame loop, input handling | ~200 |
| `view/game_view.py` | All rendering logic | ~600 |
| `model/player.py` | Player state, affordability, victory | ~250 |
| `model/cards.py` | Card, Deck, Pyramid classes | ~250 |
| `model/tokens.py` | Token, Bag, Board classes | ~400 |

### 🎨 Code Style

- **Type hints required** for all new Python files (workspace rule)
- **pytest** for all tests (workspace rule)
- Use **dataclasses** for data structures
- Use **match/case** for state handling (Python 3.10+)
- Keep **stateless** functions in `GameStateManager`
- Keep **state mutations** in `Desk.apply_action()`

---

## License

This is a personal project implementing the Splendor Duel board game for learning purposes.

