# Splendor Duel - Project Directory Structure

## Current Structure (January 2026)

```
SplendorDuel/                           ← Project root
├── README.md                           # Main documentation (updated)
├── pytest.ini                          # Pytest configuration
├── overall.py                          # Quick entry point
├── WHERE_I_LEFT_OFF.md                 # 📍 START HERE - Project status summary
│
├── controller/                         # 🎮 Game loop and input handling
│   ├── __init__.py
│   ├── game_controller.py              # Main Pygame loop, click handling
│   └── selection_manager.py            # Element selection logic
│
├── model/                              # 🎲 Core game logic (no UI)
│   ├── __init__.py
│   ├── actions.py                      # ActionType enum, Action class
│   ├── cards.py                        # Card, Deck, Pyramid, Royal classes
│   ├── desk.py                         # Main game engine (apply_action)
│   ├── game_state_machine.py          # State machine (stateless)
│   ├── piece.py                        # Base class for game pieces
│   ├── player.py                       # PlayerState class
│   └── tokens.py                       # Token, Bag, Board classes
│
├── view/                               # 🎨 Rendering and UI
│   ├── __init__.py
│   ├── assets.py                       # AssetManager for images
│   ├── game_view.py                    # All Pygame rendering
│   └── layout.py                       # LayoutRegistry, click detection
│
├── data/                               # 📦 Game data and assets
│   ├── box.yaml                        # Configuration file
│   ├── cards.json                      # Card definitions (67 cards)
│   ├── tokens.json                     # Token counts
│   ├── royals.json                     # Royal card definitions
│   ├── win_conditions.json             # Victory condition data
│   └── images/                         # 🖼️ Visual assets
│       ├── background.jpg
│       ├── bag.png
│       ├── board.jpg
│       ├── cards.svg
│       ├── cards1.jpg
│       ├── cards2.jpg
│       ├── cards3.jpg
│       ├── gem-icons.png
│       ├── icons.png
│       ├── privilege.png
│       ├── royal-cards.jpg
│       ├── score-tile-playerboard.jpg
│       ├── score-tile.jpg
│       └── tokens.png
│
├── tests/                              # 🧪 Unit tests (52 passing)
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   ├── test_actions.py                 # Action tests
│   ├── test_cards.py                   # Card/Deck/Pyramid tests
│   ├── test_controller.py              # Controller tests
│   ├── test_desk.py                    # Game engine tests
│   ├── test_game_state_machine.py      # State machine tests
│   ├── test_player.py                  # Player state tests
│   ├── test_royals.py                  # Royal card tests
│   ├── test_tokens.py                  # Token/Bag/Board tests
│   └── visual_asset_checker.py         # Asset loading verification
│
├── support/                            # 📚 Documentation
│   ├── ARCHITECTURE.md                 # 🏗️ System architecture overview
│   ├── classes_explanation.md          # Class responsibilities
│   ├── DEVELOPMENT_ROADMAP.md          # 🎯 Detailed task breakdown
│   ├── directory_tree.md               # This file
│   ├── QUICK_REFERENCE.md              # 📝 Cheat sheet for common tasks
│   ├── rules.txt                       # Original game rules
│   ├── state_changing.md               # State machine flow diagram
│   └── Splendor_Duel_Card_List-v3.pdf  # Official card reference
│
├── scripts/                            # 🔧 Utility scripts
│   ├── cards.json.bak                  # Backup of card data
│   ├── extract_cards.py                # Card data extraction
│   └── uppercase_cards.py              # Card data formatting
│
└── env.py                              # 🤖 Gymnasium environment (WIP)
```

## 📖 Documentation Guide

**New to the project?** Read in this order:
1. `WHERE_I_LEFT_OFF.md` - Project status and next steps
2. `README.md` - Overview and quick start
3. `support/ARCHITECTURE.md` - System design
4. `support/QUICK_REFERENCE.md` - Common tasks cheat sheet
5. `support/DEVELOPMENT_ROADMAP.md` - Detailed task breakdown

**Need help?**
- **Quick reference:** `support/QUICK_REFERENCE.md`
- **Architecture:** `support/ARCHITECTURE.md`
- **State machine:** `support/state_changing.md`
- **Game rules:** `support/rules.txt`
- **Task details:** `support/DEVELOPMENT_ROADMAP.md`

## 📊 File Statistics

| Directory | Files | Lines of Code | Purpose |
|-----------|-------|---------------|---------|
| `model/` | 7 | ~2,000 | Core game logic |
| `controller/` | 2 | ~200 | Game loop, input |
| `view/` | 3 | ~800 | Rendering, UI |
| `tests/` | 10 | ~1,500 | Unit tests |
| `support/` | 8 | ~2,000 | Documentation |
| **Total** | **30+** | **~6,500** | Full project |

## 🎯 Key Files by Task

### Implementing Card Abilities
- `model/game_state_machine.py` - Add states and handlers
- `model/desk.py` - Trigger and execute abilities
- `tests/test_game_state_machine.py` - Add tests

### Victory Condition Handling
- `controller/game_controller.py` - Check and enforce victory
- `view/game_view.py` - Display winner screen
- `model/player.py` - Victory logic (already exists)

### UI/Rendering Changes
- `view/game_view.py` - All rendering
- `view/layout.py` - Click detection
- `view/assets.py` - Image loading

### Game Logic Changes
- `model/desk.py` - Game state mutations
- `model/player.py` - Player state logic
- `model/cards.py` or `model/tokens.py` - Data structures

## 🔍 Finding Code

### By Feature
- **State machine:** `model/game_state_machine.py`
- **Action execution:** `model/desk.py:apply_action()`
- **Card abilities:** `model/desk.py` lines 236-244
- **Victory conditions:** `model/player.py:has_won()`
- **Token validation:** `model/tokens.py:Board.eligible_draws()`
- **Affordability:** `model/player.py:can_afford()`

### By State
Each state has 3 parts in `game_state_machine.py`:
1. **Selection rules** - Line ~66 in `SELECTION_RULES`
2. **Button handler** - Line ~330+ in `_handle_xxx_buttons()`
3. **UI buttons** - Line ~620+ in `get_current_action()`

## 🧪 Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| `model/player.py` | 8 tests | ~90% |
| `model/cards.py` | 6 tests | ~85% |
| `model/tokens.py` | 8 tests | ~90% |
| `model/desk.py` | 10 tests | ~80% |
| `model/game_state_machine.py` | 15 tests | ~75% |
| `controller/` | 5 tests | ~60% |
| **Total** | **52 tests** | **~80%** |

## 📝 Notes

- **Type hints:** Required for all new Python files (workspace rule)
- **Testing:** Use pytest (workspace rule)
- **Python version:** 3.10+ (uses match/case)
- **Dependencies:** pygame, pyyaml, pytest (see README)
- **Code style:** PEP 8, dataclasses, static methods for stateless functions

---

**Last Updated:** January 8, 2026