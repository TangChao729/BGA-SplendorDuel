# Development Roadmap - Splendor Duel

## 🎯 Current State (January 2026)

### Completed (85%)
The game is **fully playable** with the following features:
- ✅ Complete state machine with 11 working states
- ✅ All 3 mandatory actions (purchase, take tokens, reserve)
- ✅ Optional actions (privilege, replenish)
- ✅ Post-action flow (discard, royal selection)
- ✅ 2 card abilities (TURN, PRIVILEGE)
- ✅ Full Pygame GUI with layouts and click detection
- ✅ 52 passing unit tests

### Remaining Work (15%)
Three card abilities and victory handling are the main gaps.

---

## 📋 Task Breakdown

### Task 1: Implement "TAKE 2ND SAME" Ability ⏱️ 1 hour

**Description:** When purchasing a card with this ability, player takes 1 token from the board matching the card's color.

**Files to Modify:**
1. `model/game_state_machine.py`
   - Add state: `CARD_ABILITY_2ND_COLOR` (already exists in enum, line 37)
   - Add selection rules: `SelectionRules(["Token"], 1, 1, {"match_card_color": True})`
   - Add handler: `_handle_card_ability_2nd_color_buttons()`
   - Add case to `handle_button_click()`
   - Add case to `get_current_action()`

2. `model/desk.py`
   - In `apply_action()` under `PURCHASE_CARD` case (after line 244):
     ```python
     elif card.ability == "TAKE 2ND SAME":
         # Store card color in desk for validation
         self.pending_ability_card_color = card.color
         # Transition handled by controller
     ```
   - Add new action type handler for taking the token

3. `controller/game_controller.py`
   - After purchase, check if ability requires state transition

**Test Cases:**
- Purchase card with "TAKE 2ND SAME" ability
- Verify state transitions to `CARD_ABILITY_2ND_COLOR`
- Select matching token from board
- Verify token is added to player
- Verify state transitions to `POST_ACTION_CHECKS`
- Test when no matching tokens available (should skip)

---

### Task 2: Implement "STEAL" Ability ⏱️ 1 hour

**Description:** When purchasing a card with this ability, player takes 1 Gem or Pearl token from opponent (not Gold).

**Files to Modify:**
1. `model/game_state_machine.py`
   - Add state: `CARD_ABILITY_STEAL` (already exists in enum, line 39)
   - Add selection rules: `SelectionRules(["Token"], 1, 1, {"opponent_tokens_only": True, "no_gold": True})`
   - Add handler: `_handle_card_ability_steal_buttons()`
   - Add case to `handle_button_click()`
   - Add case to `get_current_action()`
   - In `can_select_element()`, add validation for opponent tokens

2. `model/desk.py`
   - In `apply_action()` under `PURCHASE_CARD` case:
     ```python
     elif card.ability == "STEAL":
         # Transition to steal state
         pass
     ```
   - Add action handler to transfer token from opponent to current player

3. `view/game_view.py`
   - Ensure opponent tokens are rendered and clickable in steal state

**Test Cases:**
- Purchase card with "STEAL" ability
- Verify state transitions to `CARD_ABILITY_STEAL`
- Select opponent's gem token
- Verify token is transferred
- Test when opponent has no valid tokens (should skip)
- Verify cannot select gold tokens

---

### Task 3: Implement "1 COLOR" (Joker) Ability ⏱️ 2-3 hours

**Description:** Most complex ability. Card must overlap an existing bonus card and takes that card's color.

**Files to Modify:**
1. `model/player.py`
   - Add method: `get_cards_with_bonus() -> List[Card]`
   - Add method: `overlap_card(joker: Card, target: Card) -> None`
   - Add attribute: `card_overlaps: Dict[str, str]` (joker_id -> target_id)
   - Modify `get_bonuses()` to account for overlapped jokers
   - Modify `can_afford()` to check if player has cards to overlap

2. `model/game_state_machine.py`
   - Add state: `CARD_ABILITY_JOKER` (already exists in enum, line 36)
   - Add selection rules: `SelectionRules(["Card"], 1, 1, {"player_cards_with_bonus": True})`
   - Add handler: `_handle_card_ability_joker_buttons()`
   - Add case to `handle_button_click()`
   - Add case to `get_current_action()`
   - In `can_select_element()`, validate card has bonus

3. `model/desk.py`
   - In `apply_action()` under `PURCHASE_CARD` case (line 243):
     ```python
     elif card.ability == "1 COLOR" or card.ability == "1 COLOR/TURN":
         if card.ability == "1 COLOR/TURN":
             self.grant_extra_turn()
         # Check if player has cards with bonus
         if not player.get_cards_with_bonus():
             return  # Cannot purchase, but this should be prevented earlier
         # Store joker card for overlap selection
         self.pending_joker_card = card
         # Transition to CARD_ABILITY_JOKER state
     ```
   - Add action handler to apply overlap

4. `view/game_view.py`
   - Render player's purchased cards as clickable in joker state
   - Visual indication of overlap (card positioning)

**Test Cases:**
- Attempt to purchase joker without bonus cards (should be disabled)
- Purchase joker with bonus cards available
- Verify state transitions to `CARD_ABILITY_JOKER`
- Select target card to overlap
- Verify joker takes target's color
- Verify bonuses calculated correctly
- Test "1 COLOR/TURN" combo ability

---

### Task 4: Victory Condition Enforcement ⏱️ 1-2 hours

**Description:** Check victory conditions at end of turn and display winner.

**Files to Modify:**
1. `controller/game_controller.py`
   - In `_handle_action_button_click()`, after `finish_round`:
     ```python
     # Check victory conditions
     if self.desk.current_player.has_won():
         self.session_state = session_state.with_state(GameState.GAME_OVER)
         self.add_message(f"{self.desk.current_player.name} wins!")
         return None
     ```

2. `model/game_state_machine.py`
   - Add state: `GAME_OVER = "game_over"`
   - Add handler to display winner and restart option

3. `view/game_view.py`
   - Add victory screen overlay
   - Display winning condition (20 points, 10 crowns, or 10 points same color)
   - Show restart button

**Test Cases:**
- Win by 20 prestige points
- Win by 10 crowns
- Win by 10 points same color
- Verify game stops accepting input after victory
- Test restart functionality

---

### Task 5: Rollback Prevention ⏱️ 1 hour

**Description:** After replenishing board or reserving face-down cards, prevent rollback to start of round.

**Files to Modify:**
1. `model/desk.py`
   - Add attribute: `committed_action: bool = False`
   - Set to `True` after replenish or face-down reserve

2. `model/game_state_machine.py`
   - In `_handle_confirm_round_buttons()`:
     ```python
     case "rollback_to_start":
         if desk.committed_action:
             return session, None, "Cannot rollback after committed action"
         # ... existing rollback logic
     ```
   - In `get_current_action()` for `CONFIRM_ROUND`:
     ```python
     buttons = [ActionButton("Yes", "finish_round")]
     if not desk.committed_action:
         buttons.append(ActionButton("No", "rollback_to_start"))
     ```

**Test Cases:**
- Rollback before replenish (should work)
- Rollback after replenish (should be disabled)
- Rollback after face-down reserve (should be disabled)
- Verify button doesn't appear when committed

---

### Task 6: Face-down Deck Reservations ⏱️ 30 min

**Description:** Allow clicking on face-down decks to reserve top card.

**Files to Modify:**
1. `view/game_view.py`
   - In `render()`, make deck sprites clickable in `TAKE_GOLD_AND_RESERVE` state
   - Add deck positions to layout registry

2. `model/game_state_machine.py`
   - Already handles `Deck` type in selection rules (line 73)
   - Verify deck handling in `_handle_take_gold_and_reserve_buttons()`

**Test Cases:**
- Click on deck in reserve state
- Verify top card is drawn and reserved
- Verify deck is hidden until confirmed

---

## 🧪 Testing Strategy

### Unit Tests
Each task should add tests to:
- `tests/test_game_state_machine.py` - State transitions
- `tests/test_desk.py` - Action execution
- `tests/test_player.py` - Player state changes

### Integration Tests
After all tasks:
- Full game playthrough with all abilities
- Victory condition scenarios
- Edge cases (empty board, no valid moves, etc.)

### Manual Testing Checklist
- [ ] Play full game with all abilities
- [ ] Test each victory condition
- [ ] Verify UI responsiveness
- [ ] Check message history accuracy
- [ ] Test rollback in various states
- [ ] Verify token/card counts are accurate

---

## 🚀 Deployment Checklist

Before considering the project "complete":
- [ ] All 6 tasks above completed
- [ ] All tests passing (target: 70+ tests)
- [ ] No TODO comments in code
- [ ] README updated with final status
- [ ] Code formatted and linted
- [ ] Visual assets loading correctly
- [ ] Performance acceptable (30 FPS)

---

## 🔮 Future Enhancements (Post-MVP)

These are **not required** for core game completion:

1. **AI Opponent** (10-20 hours)
   - Implement Gymnasium environment in `env.py`
   - Create random agent
   - Create heuristic agent
   - Optional: Train RL agent

2. **Network Multiplayer** (15-25 hours)
   - WebSocket server
   - Client-server architecture
   - Lobby system
   - Reconnection handling

3. **Save/Load Game** (2-3 hours)
   - Serialize desk state to JSON
   - Load from saved state
   - Auto-save feature

4. **Polish** (5-10 hours)
   - Sound effects
   - Animations (card flip, token take)
   - Better UI/UX (tooltips, hover effects)
   - Settings menu (volume, resolution)

5. **Tutorial Mode** (5-8 hours)
   - Interactive tutorial
   - Hint system
   - Rule reference in-game

---

## 📊 Progress Tracking

| Task | Status | Assignee | Completed Date |
|------|--------|----------|----------------|
| Task 1: TAKE 2ND SAME | ⬜ Not Started | - | - |
| Task 2: STEAL | ⬜ Not Started | - | - |
| Task 3: Joker (1 COLOR) | ⬜ Not Started | - | - |
| Task 4: Victory Enforcement | ⬜ Not Started | - | - |
| Task 5: Rollback Prevention | ⬜ Not Started | - | - |
| Task 6: Face-down Reservations | ⬜ Not Started | - | - |

**Legend:** ⬜ Not Started | 🟦 In Progress | ✅ Complete

---

## 💡 Tips for Implementation

1. **Start with Task 1 (TAKE 2ND SAME)** - It's the simplest ability and will establish the pattern for others.

2. **Test incrementally** - Write tests before implementing each feature.

3. **Use existing patterns** - Look at how `USE_PRIVILEGE` state works as a template.

4. **Debug with message history** - The game logs all actions to the message panel.

5. **Commit frequently** - Each task should be a separate commit.

6. **Update README** - Check off completed features as you go.

---

## 🆘 Getting Unstuck

If you get stuck on any task:

1. **Check similar implementations** - Look at existing states like `USE_PRIVILEGE` or `ROYAL_SELECTION`
2. **Review state flow** - See `support/state_changing.md`
3. **Check game rules** - See `support/rules.txt` lines 140-200
4. **Run tests** - `pytest -v` to see what's breaking
5. **Visual debugging** - Use `tests/visual_asset_checker.py` for rendering issues

---

**Last Updated:** January 8, 2026

