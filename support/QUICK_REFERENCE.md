# Quick Reference Card - Splendor Duel Development

## 🚀 Common Commands

```bash
# Run the game
python -m controller.game_controller

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_game_state_machine.py -v

# Run specific test
pytest tests/test_desk.py::test_purchase_card -v

# Run with print output (for debugging)
pytest -v -s

# Run with coverage
pytest --cov=model --cov=controller --cov=view

# Check visual assets
python tests/visual_asset_checker.py
```

---

## 📂 File Locations Cheat Sheet

| What You Need | File Path | Line |
|---------------|-----------|------|
| Add new game state | `model/game_state_machine.py` | 13-42 |
| Add selection rules | `model/game_state_machine.py` | 66-79 |
| Add button handler | `model/game_state_machine.py` | 283-329 |
| Add UI buttons | `model/game_state_machine.py` | 615-735 |
| Execute actions | `model/desk.py` | 177-270 |
| Card abilities trigger | `model/desk.py` | 236-244 |
| Player state logic | `model/player.py` | 8-250 |
| Victory conditions | `model/player.py` | 180-220 |
| Main game loop | `controller/game_controller.py` | 55-75 |
| Click handling | `controller/game_controller.py` | 77-140 |
| Rendering | `view/game_view.py` | entire file |

---

## 🎯 Adding a New Card Ability (Checklist)

### 1. Define State (game_state_machine.py)
```python
# In GameState enum (line ~35)
CARD_ABILITY_XXX = "card_ability_xxx"  # TODO -> remove TODO

# In GameStateConfig.SELECTION_RULES (line ~66)
GameState.CARD_ABILITY_XXX: SelectionRules(
    ["Token"],  # or ["Card"], etc.
    max_selections=1,
    min_selections=1,
    special_rules={"your_rule": True}
),
```

### 2. Add Handler (game_state_machine.py)
```python
# Around line ~330
@staticmethod
def _handle_card_ability_xxx_buttons(session, button, desk):
    match button.action:
        case "confirm":
            # Validate selection
            # Create action
            # Return new session + action
        case "cancel":
            # Return to previous state
```

### 3. Wire Up Handler (game_state_machine.py)
```python
# In handle_button_click() match statement (line ~292)
case GameState.CARD_ABILITY_XXX:
    return GameStateManager._handle_card_ability_xxx_buttons(session, button, desk)

# In get_current_action() match statement (line ~621)
case GameState.CARD_ABILITY_XXX:
    explanation = "Select X to do Y"
    buttons = [
        ActionButton("Confirm", "confirm", enabled=...),
        ActionButton("Cancel", "cancel")
    ]
    return CurrentAction(session.current_state, explanation, buttons)
```

### 4. Trigger from Purchase (desk.py)
```python
# In apply_action() under PURCHASE_CARD case (line ~236)
elif card.ability == "YOUR_ABILITY_NAME":
    # Store any needed context
    self.pending_ability_data = {...}
    # State transition handled by controller
    # Controller will check and transition to CARD_ABILITY_XXX
```

### 5. Execute Ability (desk.py)
```python
# In apply_action() add new case (line ~177)
case ActionType.YOUR_ABILITY_ACTION:
    # Get data from action.payload
    # Modify game state
    # Update player state
```

### 6. Add Tests (tests/test_game_state_machine.py)
```python
def test_card_ability_xxx_flow():
    # Setup
    # Trigger ability
    # Assert state transition
    # Confirm selection
    # Assert action created
    # Assert state after
```

---

## 🔍 Common Code Patterns

### Pattern 1: Single Element Selection (e.g., Royal, Card)
```python
# Selection rules
SelectionRules(["Royal"], 1, 1)

# Handler
selected_element = session.current_selection[0]
item = selected_element.element
metadata = selected_element.metadata
```

### Pattern 2: Multiple Element Selection (e.g., Tokens)
```python
# Selection rules
SelectionRules(["Token"], 3, 1)  # max 3, min 1

# Handler
items = [elem.element for elem in session.current_selection]
```

### Pattern 3: Conditional Button Enable
```python
ActionButton(
    "Confirm",
    "confirm",
    enabled=rules.has_minimum_selections(len(session.current_selection))
)
```

### Pattern 4: State Transition with Action
```python
new_session = session.with_state_and_selection(GameState.NEXT_STATE, [])
action = Action(ActionType.MY_ACTION, {"data": value})
return new_session, action, "Success message"
```

### Pattern 5: State Transition without Action
```python
new_session = session.with_state(GameState.NEXT_STATE)
return new_session, None, "Transitioned to next state"
```

---

## 🧪 Testing Patterns

### Pattern 1: State Transition Test
```python
def test_state_transition():
    desk = create_test_desk()
    session = GameSessionState(GameState.START, [])
    button = ActionButton("Action", "action_name")
    
    new_session, action, msg = GameStateManager.handle_button_click(
        session, button, desk
    )
    
    assert new_session.current_state == GameState.EXPECTED
    assert action is None  # or check action
    assert "expected message" in msg.lower()
```

### Pattern 2: Action Execution Test
```python
def test_action_execution():
    desk = create_test_desk()
    player = desk.current_player
    
    # Setup
    initial_state = player.some_value
    
    # Execute
    action = Action(ActionType.MY_ACTION, {"data": value})
    desk.apply_action(action)
    
    # Assert
    assert player.some_value == expected_value
    assert player.some_value != initial_state
```

### Pattern 3: Selection Validation Test
```python
def test_selection_validation():
    desk = create_test_desk()
    session = GameSessionState(GameState.MY_STATE, [])
    element = LayoutElement(...)
    
    can_select, reason = GameStateManager.can_select_element(
        session, element, desk
    )
    
    assert can_select == True  # or False
    assert reason == ""  # or expected error message
```

---

## 🎨 Data Structure Quick Reference

### GameSessionState
```python
session = GameSessionState(
    current_state=GameState.XXX,
    current_selection=[LayoutElement(...), ...]
)

# Immutable updates
new_session = session.with_state(GameState.YYY)
new_session = session.with_selection([...])
new_session = session.with_state_and_selection(GameState.YYY, [...])
```

### Action
```python
action = Action(
    type=ActionType.XXX,
    payload={
        "key": value,
        "token": token_obj,
        "card": card_obj,
        # ... any data needed
    }
)
```

### LayoutElement
```python
element = LayoutElement(
    element=actual_object,  # Token, Card, etc.
    element_type=type(actual_object),
    name="Display Name",
    rect=pygame.Rect(...),
    metadata={
        "position": (row, col),
        "level": 1,
        "index": 0,
        "player": "Player 1",
        # ... any context data
    }
)
```

### SelectionRules
```python
rules = SelectionRules(
    allowed_types=["Token", "Card"],  # Type names
    max_selections=3,
    min_selections=1,
    special_rules={
        "no_gold": True,
        "player_tokens_only": True,
        "opponent_tokens_only": True,
        "discard_mode": True,
        # ... custom rules
    }
)
```

---

## 🐛 Debugging Checklist

When something doesn't work:

- [ ] Check message history (bottom of game window)
- [ ] Print `session_state.current_state` to see current state
- [ ] Print `session_state.current_selection` to see what's selected
- [ ] Print `desk.to_dict()` to see full game state
- [ ] Run tests: `pytest -v -s` to see print output
- [ ] Check if state is in `GameStateConfig.SELECTION_RULES`
- [ ] Check if handler is wired up in `handle_button_click()`
- [ ] Check if UI buttons are defined in `get_current_action()`
- [ ] Check if action type is handled in `desk.apply_action()`
- [ ] Verify element type name matches exactly (case-sensitive)

---

## 📊 Game State Flow Diagram

```
START_OF_ROUND
    ↓ (optional)
USE_PRIVILEGE → back to START_OF_ROUND
    ↓ (optional)
REPLENISH_BOARD
    ↓
CHOOSE_MANDATORY_ACTION
    ↓
[PURCHASE_CARD | TAKE_TOKENS | TAKE_GOLD_AND_RESERVE]
    ↓
POST_ACTION_CHECKS
    ↓ (if qualified)
ROYAL_SELECTION
    ↓
CHECK_DISCARD
    ↓ (if >10 tokens)
DISCARD_TOKENS → back to CHECK_DISCARD
    ↓
CONFIRM_ROUND → back to START_OF_ROUND (next player)
```

**Missing states to implement:**
- `CARD_ABILITY_2ND_COLOR` (after PURCHASE_CARD, before POST_ACTION_CHECKS)
- `CARD_ABILITY_STEAL` (after PURCHASE_CARD, before POST_ACTION_CHECKS)
- `CARD_ABILITY_JOKER` (after PURCHASE_CARD, before POST_ACTION_CHECKS)
- `GAME_OVER` (after CONFIRM_ROUND if victory)

---

## 🎲 Card Abilities Reference

| Ability Name | JSON Value | Effect | State Needed |
|--------------|-----------|--------|--------------|
| Extra Turn | `"TURN"` | Take another turn | None (auto) ✅ |
| Privilege | `"PRIVILEGE"` | Gain 1 privilege | None (auto) ✅ |
| Take Token | `"TAKE 2ND SAME"` | Take 1 token matching card color | `CARD_ABILITY_2ND_COLOR` ❌ |
| Steal | `"STEAL"` | Steal 1 gem/pearl from opponent | `CARD_ABILITY_STEAL` ❌ |
| Joker | `"1 COLOR"` | Overlap bonus card, take its color | `CARD_ABILITY_JOKER` ❌ |
| Combo | `"1 COLOR/TURN"` | Joker + Extra Turn | `CARD_ABILITY_JOKER` ❌ |

✅ = Implemented | ❌ = Not Implemented

---

## 🔢 Victory Conditions

Checked in `player.py:has_won()`:

1. **20+ Prestige Points** - Sum of all card points + royal points
2. **10+ Crowns** - Sum of all card crowns + royal crowns
3. **10+ Points Same Color** - Points from cards of one color (jokers count)

Currently checked but **not enforced** in game loop.

---

## 📦 Dependencies

```bash
# Required
pip install pygame pyyaml pytest

# Optional (for RL environment)
pip install gymnasium
```

---

## 🎯 Next Task Reminder

**Start with:** Task 1 - Implement "TAKE 2ND SAME" ability

**Files to modify:**
1. `model/game_state_machine.py` (add handler, wire up)
2. `model/desk.py` (trigger and execute)
3. `tests/test_game_state_machine.py` (add tests)

**Estimated time:** 1 hour

**See:** `support/DEVELOPMENT_ROADMAP.md` Task 1 for detailed instructions

---

**Last Updated:** January 8, 2026

