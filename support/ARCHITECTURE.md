# Architecture Overview - Splendor Duel

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                          │
│                    (Mouse Clicks, Keys)                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    CONTROLLER LAYER                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           GameController (game_controller.py)         │  │
│  │  • Pygame event loop                                  │  │
│  │  • Interprets clicks via LayoutRegistry              │  │
│  │  • Manages GameSessionState (current state + selection)│ │
│  │  • Calls GameStateManager for state transitions      │  │
│  │  • Applies actions to Desk                           │  │
│  │  • Triggers GameView for rendering                   │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│      MODEL LAYER         │  │      VIEW LAYER          │
│  ┌────────────────────┐  │  │  ┌────────────────────┐  │
│  │ GameStateManager   │  │  │  │ GameView           │  │
│  │ (stateless)        │  │  │  │ • Renders desk     │  │
│  │ • State transitions│  │  │  │ • Draws UI         │  │
│  │ • Selection rules  │  │  │  │ • Layout registry  │  │
│  │ • Button handling  │  │  │  │ • Asset manager    │  │
│  └────────────────────┘  │  │  └────────────────────┘  │
│  ┌────────────────────┐  │  │                          │
│  │ Desk               │  │  │                          │
│  │ (game engine)      │  │  │                          │
│  │ • Applies actions  │  │  │                          │
│  │ • Holds game state │  │  │                          │
│  │ • Pyramid, Board   │  │  │                          │
│  │ • Players, Royals  │  │  │                          │
│  └────────────────────┘  │  │                          │
└──────────────────────────┘  └──────────────────────────┘
```

---

## 📦 Module Breakdown

### Controller Layer (`controller/`)

#### `GameController` (game_controller.py)
**Responsibility:** Orchestrate the game loop

```python
class GameController:
    def __init__(self, card_json, token_json, royal_json, ...):
        self.desk = Desk(...)              # Game state
        self.view = GameView(...)          # Renderer
        self.session_state = GameSessionState(...)  # UI state
        self.message_history = []          # Action log
    
    def run(self):
        """Main Pygame loop"""
        while self.running:
            # Handle events
            # Render view
            # Tick clock
    
    def _interpret_click(self, pos):
        """Map click to action"""
        # Find element at position
        # Handle selection or button click
        # Return action to execute
```

**Key Methods:**
- `run()` - Main game loop
- `_interpret_click()` - Handle mouse clicks
- `_handle_element_selection()` - Update selection state
- `_handle_action_button_click()` - Process button actions

---

### Model Layer (`model/`)

#### `Desk` (desk.py)
**Responsibility:** Core game engine, holds all game state

```python
class Desk:
    def __init__(self, card_json, token_json, royal_json, ...):
        self.pyramid = Pyramid(...)        # 3-level card pyramid
        self.board = Board()               # 5x5 token grid
        self.bag = Bag(...)                # Token supply
        self.royals = {...}                # Royal cards
        self.players = [...]               # Two players
        self.current_player_index = 0      # Current turn
        self.privileges = 3                # Scrolls on table
        self.extra_turn = False            # TURN ability flag
    
    def apply_action(self, action: Action):
        """Execute game action (mutates state)"""
        match action.type:
            case ActionType.PURCHASE_CARD:
                # Buy card, trigger abilities
            case ActionType.TAKE_TOKENS:
                # Take tokens, grant privilege if needed
            # ... etc
```

**Key Methods:**
- `apply_action()` - Execute actions (only place state mutates)
- `next_player()` - Advance turn
- `grant_extra_turn()` / `has_extra_turn()` - TURN ability
- `grant_privilege_to_player()` - Give privilege scroll

**State Held:**
- Pyramid (cards)
- Board (tokens)
- Bag (token supply)
- Players (2)
- Royals (4 slots)
- Privileges (scrolls)

---

#### `GameStateManager` (game_state_machine.py)
**Responsibility:** Stateless state machine logic

```python
class GameStateManager:
    @staticmethod
    def get_selection_rules(state: GameState) -> SelectionRules:
        """Get what can be selected in this state"""
    
    @staticmethod
    def can_select_element(session, element, desk) -> (bool, str):
        """Check if element can be selected"""
    
    @staticmethod
    def select_element(session, element, desk) -> (GameSessionState, bool, str):
        """Attempt to select/deselect element"""
    
    @staticmethod
    def handle_button_click(session, button, desk) -> (GameSessionState, Action, str):
        """Process button click, return new state + action"""
        match session.current_state:
            case GameState.START_OF_ROUND:
                return _handle_start_of_round_buttons(...)
            case GameState.USE_PRIVILEGE:
                return _handle_use_privilege_buttons(...)
            # ... etc
    
    @staticmethod
    def get_current_action(session, desk) -> CurrentAction:
        """Get UI buttons for current state"""
```

**Key Concepts:**
- **Stateless** - All functions are static, no instance state
- **Pure functions** - Same input always produces same output
- **Immutable updates** - Returns new `GameSessionState`, never mutates
- **Separation of concerns** - UI logic separate from game logic

---

#### `PlayerState` (player.py)
**Responsibility:** Player state and logic

```python
class PlayerState:
    def __init__(self, name: str):
        self.name = name
        self.tokens: Dict[Token, int] = {}     # Tokens held
        self.bonuses: Dict[str, int] = {}      # Permanent bonuses
        self.purchased: List[Card] = []        # Bought cards
        self.reserved: List[Card] = []         # Reserved cards (max 3)
        self.privileges = 0                    # Scrolls held
        self.royals: List[Royal] = []          # Royal cards
        self.royals_claimed_at = []            # Crown milestones
    
    def can_afford(self, card: Card) -> bool:
        """Check if player can buy card"""
    
    def pay_for_card(self, card: Card, bag: Bag):
        """Pay cost, add card, update bonuses"""
    
    def has_won(self) -> bool:
        """Check victory conditions"""
    
    def qualifies_for_royal(self) -> bool:
        """Check if reached 3 or 6 crowns"""
```

**Key Methods:**
- `can_afford()` - Check affordability (bonuses + gold)
- `pay_for_card()` - Execute purchase
- `has_won()` - Check 3 victory conditions
- `qualifies_for_royal()` - Check crown milestones
- `get_token_count()` - Total tokens (for discard check)

---

#### `Card`, `Deck`, `Pyramid` (cards.py)
**Responsibility:** Card data and management

```python
class Card:
    def __init__(self, id, level, color, points, bonus, ability, crowns, cost):
        self.id = id                   # "1-01"
        self.level = level             # 1, 2, or 3
        self.color = color             # "BLACK", "RED", etc.
        self.points = points           # Prestige points
        self.bonus = bonus             # Permanent gem bonus
        self.ability = ability         # "TURN", "STEAL", etc.
        self.crowns = crowns           # Crown count
        self.cost = cost               # {Token: int}

class Deck:
    def __init__(self, cards: List[Card]):
        self.cards = cards
    
    def shuffle(self):
        """Randomize order"""
    
    def draw(self, n: int) -> List[Card]:
        """Draw n cards from top"""

class Pyramid:
    def __init__(self, decks: Dict[int, Deck]):
        self.levels = {1: [], 2: [], 3: []}  # Cards in pyramid
        self.decks = decks                   # Face-down decks
    
    def fill_card(self, level: int, index: int):
        """Replace card from deck"""
```

---

#### `Token`, `Bag`, `Board` (tokens.py)
**Responsibility:** Token data and board management

```python
class Token:
    def __init__(self, color: str):
        self.color = color  # "black", "red", ..., "gold", "pearl"

class Bag:
    def __init__(self, tokens: Dict[Token, int]):
        self.tokens = tokens
    
    def draw(self) -> List[Token]:
        """Draw all tokens (for board refill)"""
    
    def return_tokens(self, tokens: List[Token]):
        """Return tokens to bag"""

class Board:
    def __init__(self):
        self.grid = [[None]*5 for _ in range(5)]  # 5x5 grid
    
    def fill_grid(self, tokens: List[Token]):
        """Place tokens on board"""
    
    def eligible_draws(self) -> List[Dict[Token, List[Tuple]]]:
        """Get all valid token combinations"""
    
    def draw(self, combo: Dict[Token, List[Tuple]]) -> List[Token]:
        """Take tokens from board"""
```

**Key Concepts:**
- Board is 5x5 grid
- Tokens must be adjacent in straight line
- `eligible_draws()` computes all valid combinations
- Bag refills board when empty

---

### View Layer (`view/`)

#### `GameView` (game_view.py)
**Responsibility:** All rendering

```python
class GameView:
    def __init__(self, screen, assets):
        self.screen = screen
        self.assets = assets
        self.layout_registry = LayoutRegistry()
    
    def render(self, desk, messages, current_action, selection):
        """Main render function"""
        self.layout_registry.clear()
        
        # Render main panel (board, pyramid, royals)
        self._render_main_panel(desk)
        
        # Render player panels
        self._render_player_panel(desk.players[0], ...)
        self._render_player_panel(desk.players[1], ...)
        
        # Render action panel (buttons)
        self._render_action_panel(current_action)
        
        # Render message history
        self._render_messages(messages)
        
        pygame.display.flip()
```

**Key Methods:**
- `render()` - Main entry point
- `_render_main_panel()` - Board, pyramid, royals, bag
- `_render_player_panel()` - Tokens, cards, reserved
- `_render_action_panel()` - Buttons for current state
- `_render_messages()` - Action log

**Layout System:**
- `LayoutRegistry` - Tracks clickable elements
- `LayoutElement` - Wraps game object + rect + metadata
- Click detection via `find_element_at(pos)`

---

#### `AssetManager` (assets.py)
**Responsibility:** Load and manage images

```python
class AssetManager:
    def __init__(self, asset_path: str):
        self.asset_path = asset_path
        self.images = {}
    
    def load_image(self, filename: str) -> pygame.Surface:
        """Load image, cache in memory"""
    
    def get_card_sprite(self, card: Card) -> pygame.Surface:
        """Get sprite for card"""
    
    def get_token_sprite(self, token: Token) -> pygame.Surface:
        """Get sprite for token"""
```

---

## 🔄 Data Flow

### User Clicks Element

```
1. User clicks at (x, y)
   ↓
2. GameController._interpret_click(pos)
   ↓
3. LayoutRegistry.find_element_at(pos) → LayoutElement
   ↓
4. If element (not button):
      GameStateManager.select_element(session, element, desk)
      → Returns new GameSessionState
   ↓
5. If button:
      GameStateManager.handle_button_click(session, button, desk)
      → Returns (new GameSessionState, Action, message)
   ↓
6. If action returned:
      desk.apply_action(action)
      → Mutates desk state
   ↓
7. GameView.render(desk, messages, current_action, selection)
   → Draws updated state
```

### State Transition Example: Use Privilege

```
1. State: START_OF_ROUND
   User clicks "Use Privilege" button
   ↓
2. GameStateManager.handle_button_click()
   → _handle_start_of_round_buttons()
   → Returns (new session with USE_PRIVILEGE state, None, message)
   ↓
3. GameView renders with USE_PRIVILEGE state
   → Shows "Select token" message
   → Board tokens become clickable
   ↓
4. User clicks token
   ↓
5. GameStateManager.select_element()
   → Validates token selection (no gold)
   → Returns new session with token in selection
   ↓
6. User clicks "Confirm" button
   ↓
7. GameStateManager.handle_button_click()
   → _handle_use_privilege_buttons()
   → Creates Action(USE_PRIVILEGE, {token, position})
   → Returns (new session with START_OF_ROUND state, action, message)
   ↓
8. desk.apply_action(action)
   → player.add_token(token)
   → board.remove_token(position)
   → player.privileges -= 1
   ↓
9. GameView renders updated state
```

---

## 🎯 Key Design Patterns

### 1. **Stateless State Machine**
`GameStateManager` has no instance state. All functions are static and pure.

**Benefits:**
- Easier to test (no setup needed)
- No hidden state bugs
- Clear data flow
- Easy to reason about

### 2. **Immutable Session State**
`GameSessionState` is immutable. Updates return new instances.

```python
# Bad (mutable)
session.current_state = GameState.NEW_STATE

# Good (immutable)
new_session = session.with_state(GameState.NEW_STATE)
```

**Benefits:**
- Can't accidentally mutate state
- Easy to implement undo/redo
- Thread-safe (if needed)

### 3. **Single Source of Truth**
`Desk` is the only place game state is mutated.

**Benefits:**
- Easy to debug (one place to look)
- Easy to serialize/save game
- Clear ownership of state

### 4. **Separation of Concerns**
- **Model** - Game logic, no UI code
- **View** - Rendering, no game logic
- **Controller** - Glue between model and view

**Benefits:**
- Easy to test model without UI
- Easy to change UI without breaking logic
- Could swap Pygame for web UI

### 5. **Layout Registry**
View registers clickable elements, controller queries on click.

**Benefits:**
- Decouples rendering from click handling
- Easy to make anything clickable
- Supports complex layouts

---

## 📊 State Machine Details

### States (11 implemented, 4 missing)

```
✅ START_OF_ROUND          - Choose action
✅ USE_PRIVILEGE           - Select token with privilege
✅ REPLENISH_BOARD         - Confirm board refill
✅ CHOOSE_MANDATORY_ACTION - Choose mandatory action
✅ PURCHASE_CARD           - Select card to buy
✅ TAKE_TOKENS             - Select tokens to take
✅ TAKE_GOLD_AND_RESERVE   - Select gold + card
✅ POST_ACTION_CHECKS      - Auto-check for royal/discard
✅ CHECK_DISCARD           - Auto-check token count
✅ DISCARD_TOKENS          - Select tokens to discard
✅ ROYAL_SELECTION         - Select royal card
✅ CONFIRM_ROUND           - Confirm or rollback

❌ CARD_ABILITY_2ND_COLOR  - Select token for TAKE 2ND SAME
❌ CARD_ABILITY_STEAL      - Select opponent token for STEAL
❌ CARD_ABILITY_JOKER      - Select card to overlap for 1 COLOR
❌ GAME_OVER               - Display winner
```

### State Transitions

Each state has:
1. **Selection rules** - What can be selected
2. **Button handler** - What buttons do
3. **UI buttons** - What buttons to show
4. **Next states** - Where to go next

Example: `USE_PRIVILEGE`

```python
# 1. Selection rules
SelectionRules(["Token"], 1, 1, {"no_gold": True})

# 2. Button handler
def _handle_use_privilege_buttons(session, button, desk):
    if button.action == "confirm":
        # Create action
        # Return new state + action
    elif button.action == "cancel":
        # Return to START_OF_ROUND

# 3. UI buttons
[
    ActionButton("Confirm", "confirm", enabled=has_selection),
    ActionButton("Cancel", "cancel")
]

# 4. Next states
# confirm → START_OF_ROUND (with action)
# cancel → START_OF_ROUND (no action)
```

---

## 🧪 Testing Architecture

### Test Structure

```
tests/
├── conftest.py                    # Fixtures (create_test_desk, etc.)
├── test_game_state_machine.py    # State transition tests
├── test_desk.py                   # Action execution tests
├── test_player.py                 # Player logic tests
├── test_cards.py                  # Card/Deck/Pyramid tests
├── test_tokens.py                 # Token/Bag/Board tests
├── test_royals.py                 # Royal card tests
└── test_controller.py             # Controller integration tests
```

### Testing Layers

```
Unit Tests (model/)
├── test_player.py      - Player state logic
├── test_cards.py       - Card/Deck/Pyramid
├── test_tokens.py      - Token/Bag/Board
└── test_royals.py      - Royal cards

State Machine Tests (model/)
└── test_game_state_machine.py
    ├── State transitions
    ├── Selection validation
    ├── Button handling
    └── Action creation

Integration Tests (controller/)
└── test_controller.py
    ├── Full action flows
    ├── Multi-state sequences
    └── Edge cases

Manual Tests
└── Run game, click around
```

---

## 🔧 Extension Points

### Adding New Action Type

1. Add to `ActionType` enum in `actions.py`
2. Add case to `desk.apply_action()` in `desk.py`
3. Add tests in `test_desk.py`

### Adding New Game State

1. Add to `GameState` enum in `game_state_machine.py`
2. Add selection rules in `GameStateConfig.SELECTION_RULES`
3. Add handler `_handle_xxx_buttons()`
4. Add case to `handle_button_click()`
5. Add case to `get_current_action()`
6. Add tests in `test_game_state_machine.py`

### Adding New Card Ability

1. Add ability name to card JSON
2. Add trigger in `desk.apply_action()` under `PURCHASE_CARD`
3. Add new state (if needed) - see "Adding New Game State"
4. Add action type (if needed) - see "Adding New Action Type"
5. Add tests

### Adding New UI Element

1. Render in `GameView._render_xxx()`
2. Register in `LayoutRegistry` with metadata
3. Handle selection in `GameStateManager.can_select_element()`
4. Handle click in controller

---

## 📈 Performance Considerations

### Current Performance
- **FPS:** 30 (capped)
- **Render time:** ~5ms per frame
- **State transitions:** <1ms
- **Action execution:** <1ms

### Bottlenecks (if any)
- Asset loading (done once at startup)
- Eligible draws calculation (O(n²) but n=25)

### Optimizations Applied
- Asset caching (load once, reuse)
- Layout registry (O(1) click detection)
- Immutable state (no defensive copying)

---

## 🎨 Code Style Guide

### Python Style
- Type hints on all functions
- Dataclasses for data structures
- Match/case for state handling (Python 3.10+)
- Static methods for stateless functions
- Docstrings on all public methods

### Naming Conventions
- `snake_case` for functions/variables
- `PascalCase` for classes
- `UPPER_CASE` for constants/enums
- Private methods: `_method_name`

### File Organization
- One class per file (mostly)
- Related classes together (cards.py has Card, Deck, Pyramid)
- Tests mirror source structure

---

**Last Updated:** January 8, 2026

