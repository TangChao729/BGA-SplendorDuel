# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the game
python -m controller.game_controller

# Run all tests
pytest -v

# Run a single test file
pytest tests/test_game_state_machine.py -v

# Run a single test
pytest tests/test_desk.py::test_name -v

# Run with coverage
pytest --cov=model --cov=controller --cov=view
```

## Architecture

The project uses a strict MVC pattern:

- **`model/`** — Pure game logic, no Pygame imports. `Desk` is the single source of truth for mutable game state. `GameStateManager` is fully stateless (all static methods, returns new `GameSessionState` rather than mutating).
- **`view/`** — All Pygame rendering. `GameView.render()` is the single entry point. Registers clickable elements in `LayoutRegistry` during each render pass.
- **`controller/`** — `GameController` owns the Pygame event loop, maps clicks via `LayoutRegistry.find_element_at()`, delegates to `GameStateManager` for state transitions, and calls `Desk.apply_action()` to mutate state.

### Critical design constraints

- `GameSessionState` is immutable — use `session.with_state(...)` style constructors, never assign fields directly.
- `Desk.apply_action()` is the **only** place game state is mutated.
- `GameStateManager` methods return `(new_session, action, message)` tuples; the controller applies the action separately.

### Adding a new card ability (standard pattern)

1. Add `CARD_ABILITY_XXX` to `GameState` enum in `model/game_state_machine.py`
2. Add selection rules in `GameStateConfig.SELECTION_RULES`
3. Add `_handle_xxx_buttons()` handler and wire into `handle_button_click()` match statement
4. Add UI buttons in `get_current_action()`
5. Trigger from `Desk.apply_action()` under the `PURCHASE_CARD` case
6. Add tests in `tests/test_game_state_machine.py` and `tests/test_desk.py`

### State machine flow

```
START_OF_ROUND → [USE_PRIVILEGE | REPLENISH_BOARD | CHOOSE_MANDATORY_ACTION]
CHOOSE_MANDATORY_ACTION → [PURCHASE_CARD | TAKE_TOKENS | TAKE_GOLD_AND_RESERVE]
→ POST_ACTION_CHECKS → ROYAL_SELECTION? → CHECK_DISCARD → DISCARD_TOKENS? → CONFIRM_ROUND
→ START_OF_ROUND (next player)
```

See `support/state_changing.md` for detailed transition diagrams.

## Code style

- Type hints required on all functions
- `dataclass` for data structures, `match/case` for state handling (Python 3.10+)
- Static methods for stateless functions in `GameStateManager`
- Tests in `tests/conftest.py` provide shared fixtures (`create_test_desk`, etc.)

## Key files

| File | Purpose |
|------|---------|
| `model/desk.py` | Core game engine; all state mutation |
| `model/game_state_machine.py` | State transitions, selection rules, UI button logic |
| `controller/game_controller.py` | Pygame loop, click dispatch |
| `view/game_view.py` | All rendering; populates `LayoutRegistry` |
| `model/player.py` | Affordability checks, victory conditions |
| `data/box.yaml` | Top-level config pointing to JSON data files |

## Current status (branch `complete-game-logic`)

Recently completed (Jan 2026):
- `TAKE 2ND SAME` card ability (`f931616`)
- `STEAL` card ability (`fc38b4c`)
- `JOKER (1 COLOR)` card ability (`aa505ab`)
- Win condition enforcement + `GAME_OVER` state (`ad662d5`)
- Privilege bug fixes: USE_PRIVILEGE now returns scroll to table; TAKE_TOKENS correctly grants opponent a privilege on 3-same or 2-pearl draws (`685d63a`)
- Purchase-from-reserved now correctly omits `level`/`index` and uses `reserved_index` in the action payload (`685d63a`)

Still incomplete:
- Rollback prevention — players can always rollback at `CONFIRM_ROUND` even after committing actions like `REPLENISH_BOARD`
- Face-down deck reservations — UI doesn't make decks clickable; only visible pyramid cards can be reserved
