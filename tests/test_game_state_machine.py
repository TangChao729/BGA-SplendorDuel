import pytest
from unittest.mock import Mock, MagicMock
from model.game_state_machine import (
    GameState, SelectionRules, GameStateConfig, CurrentAction, GameStateMachine
)
from model.actions import Action, ActionType, ActionButton
from model.tokens import Token
from model.cards import Card


class TestGameState:
    """Test the GameState enum."""
    
    def test_game_state_enum_values(self):
        """Test that all game state enum values are correct."""
        assert GameState.START_OF_ROUND.value == "start_of_round"
        assert GameState.USE_PRIVILEGE.value == "use_privilege"
        assert GameState.REPLENISH_BOARD.value == "replenish_board"
        assert GameState.CHOOSE_MANDATORY_ACTION.value == "choose_mandatory_action"
        assert GameState.PURCHASE_CARD.value == "purchase_card"
        assert GameState.TAKE_TOKENS.value == "take_tokens"
        assert GameState.TAKE_GOLD_AND_RESERVE.value == "take_gold_and_reserve"
        assert GameState.POST_ACTION_CHECKS.value == "post_action_checks"
        assert GameState.CONFIRM_ROUND.value == "confirm_round"


class TestSelectionRules:
    """Test the SelectionRules class."""
    
    def test_selection_rules_init(self):
        """Test SelectionRules initialization."""
        rules = SelectionRules(["Token", "Card"], 3, 1, {"special": True})
        assert rules.allowed_types == ["Token", "Card"]
        assert rules.max_selections == 3
        assert rules.min_selections == 1
        assert rules.special_rules == {"special": True}
    
    def test_selection_rules_defaults(self):
        """Test SelectionRules with default values."""
        rules = SelectionRules(["Token"], 2)
        assert rules.min_selections == 0
        assert rules.special_rules is None
    
    def test_can_select_type(self):
        """Test type selection validation."""
        rules = SelectionRules(["Token", "Card"], 3)
        assert rules.can_select_type("Token")
        assert rules.can_select_type("Card")
        assert not rules.can_select_type("Other")
    
    def test_can_select_more(self):
        """Test maximum selection validation."""
        rules = SelectionRules(["Token"], 3)
        assert rules.can_select_more(0)
        assert rules.can_select_more(2)
        assert not rules.can_select_more(3)
        assert not rules.can_select_more(4)
    
    def test_has_minimum_selections(self):
        """Test minimum selection validation."""
        rules = SelectionRules(["Token"], 3, 2)
        assert not rules.has_minimum_selections(0)
        assert not rules.has_minimum_selections(1)
        assert rules.has_minimum_selections(2)
        assert rules.has_minimum_selections(3)


class TestGameStateConfig:
    """Test the GameStateConfig class."""
    
    def test_get_selection_rules_all_states(self):
        """Test that selection rules exist for all game states."""
        for state in GameState:
            rules = GameStateConfig.get_selection_rules(state)
            assert isinstance(rules, SelectionRules)
    
    def test_specific_selection_rules(self):
        """Test specific selection rules for key states."""
        # START_OF_ROUND should allow no selections
        rules = GameStateConfig.get_selection_rules(GameState.START_OF_ROUND)
        assert rules.allowed_types == []
        assert rules.max_selections == 0
        
        # USE_PRIVILEGE should allow one token
        rules = GameStateConfig.get_selection_rules(GameState.USE_PRIVILEGE)
        assert rules.allowed_types == ["Token"]
        assert rules.max_selections == 1
        assert rules.min_selections == 1
        
        # TAKE_TOKENS should allow up to 3 tokens
        rules = GameStateConfig.get_selection_rules(GameState.TAKE_TOKENS)
        assert rules.allowed_types == ["Token"]
        assert rules.max_selections == 3
        assert rules.min_selections == 1
        assert rules.special_rules == {"no_gold": True}
    
    def test_can_select_element(self):
        """Test element selection validation."""
        # Test token selection in TAKE_TOKENS state
        assert GameStateConfig.can_select_element(
            GameState.TAKE_TOKENS, "Token", 0
        )
        assert GameStateConfig.can_select_element(
            GameState.TAKE_TOKENS, "Token", 2
        )
        assert not GameStateConfig.can_select_element(
            GameState.TAKE_TOKENS, "Token", 3
        )
        assert not GameStateConfig.can_select_element(
            GameState.TAKE_TOKENS, "Card", 0
        )
    
    def test_unknown_state_fallback(self):
        """Test fallback for unknown states."""
        # Using a mock state that doesn't exist in the rules
        class MockState:
            pass
        
        rules = GameStateConfig.get_selection_rules(MockState())
        assert rules.allowed_types == []
        assert rules.max_selections == 0


class TestCurrentAction:
    """Test the CurrentAction class."""
    
    def test_current_action_init(self):
        """Test CurrentAction initialization."""
        buttons = [ActionButton("Test", "test")]
        action = CurrentAction(GameState.START_OF_ROUND, "Test explanation", buttons)
        assert action.state == GameState.START_OF_ROUND
        assert action.explanation == "Test explanation"
        assert action.buttons == buttons
    
    def test_current_action_state_conversion(self):
        """Test that state values are converted to GameState enum."""
        action = CurrentAction("start_of_round", "Test", [])
        assert action.state == GameState.START_OF_ROUND
        assert isinstance(action.state, GameState)


class TestGameStateMachine:
    """Test the GameStateMachine class."""
    
    @pytest.fixture
    def mock_desk(self):
        """Create a mock desk for testing."""
        desk = Mock()
        desk.current_player = Mock()
        desk.current_player.privileges = 0
        desk.current_player.reserved = []
        desk.current_player.can_afford = Mock(return_value=True)
        
        desk.bag = Mock()
        desk.bag.is_empty = Mock(return_value=False)
        
        desk.board = Mock()
        desk.board.counts = Mock(return_value={Token("gold"): 2, Token("red"): 5})
        desk.board.eligible_draws = Mock(return_value=[])
        
        desk.next_player = Mock()
        return desk
    
    @pytest.fixture
    def state_machine(self, mock_desk):
        """Create a GameStateMachine for testing."""
        return GameStateMachine(mock_desk)
    
    def test_init(self, mock_desk):
        """Test GameStateMachine initialization."""
        sm = GameStateMachine(mock_desk)
        assert sm.desk == mock_desk
        assert sm.current_state == GameState.START_OF_ROUND
        assert sm.current_selection == []
    
    def test_get_selection_rules(self, state_machine):
        """Test getting selection rules."""
        # Test current state
        rules = state_machine.get_selection_rules()
        assert isinstance(rules, SelectionRules)
        
        # Test specific state
        rules = state_machine.get_selection_rules(GameState.USE_PRIVILEGE)
        assert rules.allowed_types == ["Token"]
        assert rules.max_selections == 1
    
    def test_can_select_element_basic(self, state_machine):
        """Test basic element selection validation."""
        # Set state to allow token selection
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        # Mock layout element
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        
        can_select, reason = state_machine.can_select_element(layout_element, "Token")
        assert can_select
        assert reason == ""
    
    def test_can_select_element_wrong_type(self, state_machine):
        """Test element selection with wrong type."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        layout_element = Mock()
        layout_element.element = Mock()
        
        can_select, reason = state_machine.can_select_element(layout_element, "Card")
        assert not can_select
        assert "Cannot select Card" in reason
    
    def test_can_select_element_max_reached(self, state_machine):
        """Test element selection when max is reached."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        # Add one element to reach max
        mock_element = Mock()
        state_machine.current_selection = [mock_element]
        
        layout_element = Mock()
        layout_element.element = Mock()
        
        can_select, reason = state_machine.can_select_element(layout_element, "Token")
        assert not can_select
        assert "Cannot select more than" in reason
    
    def test_can_select_element_special_rules_no_gold(self, state_machine):
        """Test special rule: no gold tokens."""
        state_machine.current_state = GameState.TAKE_TOKENS
        
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "gold"
        
        can_select, reason = state_machine.can_select_element(layout_element, "Token")
        assert not can_select
        assert "Cannot select gold tokens" in reason
    
    def test_can_select_element_special_rules_require_gold(self, state_machine):
        """Test special rule: require gold first."""
        state_machine.current_state = GameState.TAKE_GOLD_AND_RESERVE
        
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        
        can_select, reason = state_machine.can_select_element(layout_element, "Token")
        assert not can_select
        assert "Must select gold token first" in reason
    
    def test_select_element_success(self, state_machine):
        """Test successful element selection."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        
        success, message = state_machine.select_element(layout_element, "Token")
        assert success
        assert "Selected Token" in message
        assert layout_element in state_machine.current_selection
    
    def test_select_element_deselect(self, state_machine):
        """Test element deselection."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        
        # First select
        state_machine.current_selection = [layout_element]
        
        # Then deselect
        success, message = state_machine.select_element(layout_element, "Token")
        assert success
        assert "Deselected Token" in message
        assert layout_element not in state_machine.current_selection
    
    def test_select_element_failure(self, state_machine):
        """Test failed element selection."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        layout_element = Mock()
        layout_element.element = Mock()
        
        success, message = state_machine.select_element(layout_element, "Card")
        assert not success
        assert "Cannot select Card" in message
        assert layout_element not in state_machine.current_selection
    
    def test_can_confirm_selection_minimum_not_met(self, state_machine):
        """Test confirmation when minimum selections not met."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        state_machine.current_selection = []  # Empty, but need 1
        
        can_confirm, reason = state_machine.can_confirm_selection()
        assert not can_confirm
        assert "Must select at least 1" in reason
    
    def test_can_confirm_selection_success(self, state_machine):
        """Test successful confirmation validation."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        mock_element = Mock()
        state_machine.current_selection = [mock_element]
        
        can_confirm, reason = state_machine.can_confirm_selection()
        assert can_confirm
        assert reason == ""
    
    def test_build_combo_from_selection(self, state_machine):
        """Test building token combo from selection."""
        # Create mock layout elements with positions
        element1 = Mock()
        element1.element = Token("red")
        element1.metadata = {"position": (0, 0)}
        
        element2 = Mock()
        element2.element = Token("red")
        element2.metadata = {"position": (0, 1)}
        
        state_machine.current_selection = [element1, element2]
        
        combo, error = state_machine._build_combo_from_selection()
        assert combo is not None
        assert error == ""
        assert Token("red") in combo
        assert len(combo[Token("red")]) == 2
    
    def test_build_combo_empty_selection(self, state_machine):
        """Test building combo with empty selection."""
        state_machine.current_selection = []
        
        combo, error = state_machine._build_combo_from_selection()
        assert combo is None
        assert "No tokens selected" in error
    
    def test_build_combo_missing_position(self, state_machine):
        """Test building combo with missing position data."""
        element = Mock()
        element.element = Token("red")
        element.metadata = {}  # No position
        
        state_machine.current_selection = [element]
        
        combo, error = state_machine._build_combo_from_selection()
        assert combo is None
        assert "missing position data" in error
    
    def test_validate_token_line_single_token(self, state_machine):
        """Test token line validation with single token."""
        element = Mock()
        state_machine.current_selection = [element]
        
        result = state_machine._validate_token_line()
        assert result  # Single token should always be valid
    
    def test_validate_token_line_valid_combo(self, state_machine):
        """Test token line validation with valid combo."""
        element1 = Mock()
        element1.element = Token("red")
        element1.metadata = {"position": (0, 0)}
        
        element2 = Mock()
        element2.element = Token("red")
        element2.metadata = {"position": (0, 1)}
        
        state_machine.current_selection = [element1, element2]
        
        # Mock the desk to return this combo as valid
        combo = {Token("red"): [(0, 0), (0, 1)]}
        state_machine.desk.board.eligible_draws.return_value = [combo]
        
        result = state_machine._validate_token_line()
        assert result
    
    def test_validate_token_line_invalid_combo(self, state_machine):
        """Test token line validation with invalid combo."""
        element1 = Mock()
        element1.element = Token("red")
        element1.metadata = {"position": (0, 0)}
        
        element2 = Mock()
        element2.element = Token("blue")
        element2.metadata = {"position": (1, 1)}
        
        state_machine.current_selection = [element1, element2]
        
        # Mock the desk to return empty eligible draws
        state_machine.desk.board.eligible_draws.return_value = []
        
        result = state_machine._validate_token_line()
        assert not result
    
    def test_transition_to_clears_selection(self, state_machine):
        """Test that transitioning to non-selection states clears selections."""
        # Add some selections
        mock_element = Mock()
        state_machine.current_selection = [mock_element]
        
        # Transition to state that doesn't allow selections
        state_machine.transition_to(GameState.START_OF_ROUND)
        
        assert state_machine.current_state == GameState.START_OF_ROUND
        assert state_machine.current_selection == []
    
    def test_transition_to_keeps_selection(self, state_machine):
        """Test that transitioning to selection states keeps selections."""
        # Add some selections
        mock_element = Mock()
        state_machine.current_selection = [mock_element]
        
        # Transition to state that allows selections
        state_machine.transition_to(GameState.USE_PRIVILEGE)
        
        assert state_machine.current_state == GameState.USE_PRIVILEGE
        assert state_machine.current_selection == [mock_element]
    
    def test_handle_button_click_unknown_state(self, state_machine):
        """Test handling button clicks in unknown state."""
        # Set to an invalid state for testing
        state_machine.current_state = "invalid_state"
        
        button = ActionButton("Test", "test")
        action, message = state_machine.handle_button_click(button)
        
        assert action is None
        assert "Unknown state" in message
    
    def test_handle_start_of_round_buttons(self, state_machine):
        """Test handling buttons in START_OF_ROUND state."""
        state_machine.current_state = GameState.START_OF_ROUND
        
        # Test use privilege button
        button = ActionButton("Use Privilege", "use_privilege")
        action, message = state_machine.handle_button_click(button)
        
        assert action is None
        assert state_machine.current_state == GameState.USE_PRIVILEGE
        assert "Select a token" in message
        
        # Test other buttons
        state_machine.current_state = GameState.START_OF_ROUND
        button = ActionButton("Replenish", "replenish_board")
        action, message = state_machine.handle_button_click(button)
        assert state_machine.current_state == GameState.REPLENISH_BOARD
    
    def test_handle_use_privilege_buttons_confirm(self, state_machine):
        """Test confirming privilege use."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        # Add a valid selection
        element = Mock()
        element.element = Token("red")
        element.metadata = {"position": (0, 0)}
        state_machine.current_selection = [element]
        
        button = ActionButton("Confirm", "confirm")
        action, message = state_machine.handle_button_click(button)
        
        assert action is not None
        assert action.type == ActionType.USE_PRIVILEGE
        assert action.payload["token"] == element.element
        assert state_machine.current_state == GameState.START_OF_ROUND
        assert "successfully" in message
    
    def test_handle_use_privilege_buttons_cancel(self, state_machine):
        """Test cancelling privilege use."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        button = ActionButton("Cancel", "cancel")
        action, message = state_machine.handle_button_click(button)
        
        assert action is None
        assert state_machine.current_state == GameState.START_OF_ROUND
        assert "Cancelled" in message
    
    def test_handle_purchase_card_buttons_confirm_success(self, state_machine):
        """Test successful card purchase confirmation."""
        state_machine.current_state = GameState.PURCHASE_CARD
        
        # Add a valid card selection
        element = Mock()
        element.element = Mock()  # Mock card
        element.metadata = {"level": 1, "index": 0}
        state_machine.current_selection = [element]
        
        # Mock player can afford the card
        state_machine.desk.current_player.can_afford.return_value = True
        
        button = ActionButton("Confirm", "confirm")
        action, message = state_machine.handle_button_click(button)
        
        assert action is not None
        assert action.type == ActionType.PURCHASE_CARD
        assert action.payload["card"] == element.element
        assert state_machine.current_state == GameState.POST_ACTION_CHECKS
    
    def test_handle_purchase_card_buttons_confirm_cannot_afford(self, state_machine):
        """Test card purchase when player cannot afford it."""
        state_machine.current_state = GameState.PURCHASE_CARD
        
        # Add a valid card selection
        element = Mock()
        element.element = Mock()  # Mock card
        element.metadata = {"level": 1, "index": 0}
        state_machine.current_selection = [element]
        
        # Mock player cannot afford the card
        state_machine.desk.current_player.can_afford.return_value = False
        
        button = ActionButton("Confirm", "confirm")
        action, message = state_machine.handle_button_click(button)
        
        assert action is None
        assert "Cannot afford" in message
    
    def test_handle_take_tokens_buttons_confirm(self, state_machine):
        """Test successful token taking confirmation."""
        state_machine.current_state = GameState.TAKE_TOKENS
        
        # Add valid token selections
        element1 = Mock()
        element1.element = Token("red")
        element1.metadata = {"position": (0, 0)}
        
        element2 = Mock()
        element2.element = Token("red")
        element2.metadata = {"position": (0, 1)}
        
        state_machine.current_selection = [element1, element2]
        
        # Mock valid combo
        combo = {Token("red"): [(0, 0), (0, 1)]}
        state_machine.desk.board.eligible_draws.return_value = [combo]
        
        button = ActionButton("Confirm", "confirm")
        action, message = state_machine.handle_button_click(button)
        
        assert action is not None
        assert action.type == ActionType.TAKE_TOKENS
        assert "combo" in action.payload
        assert state_machine.current_state == GameState.POST_ACTION_CHECKS
    
    def test_handle_confirm_round_buttons_finish(self, state_machine):
        """Test finishing a round."""
        state_machine.current_state = GameState.CONFIRM_ROUND
        
        button = ActionButton("Yes", "finish_round")
        action, message = state_machine.handle_button_click(button)
        
        assert action is None
        assert state_machine.current_state == GameState.START_OF_ROUND
        state_machine.desk.next_player.assert_called_once()
        assert "next player" in message
    
    def test_handle_confirm_round_buttons_rollback(self, state_machine):
        """Test rolling back a round."""
        state_machine.current_state = GameState.CONFIRM_ROUND
        
        button = ActionButton("No", "rollback_to_start")
        action, message = state_machine.handle_button_click(button)
        
        assert action is None
        assert state_machine.current_state == GameState.START_OF_ROUND
        assert "Rolled back" in message
    
    def test_get_current_action_start_of_round(self, state_machine):
        """Test getting current action for START_OF_ROUND state."""
        state_machine.current_state = GameState.START_OF_ROUND
        
        # Set up mock player with privilege
        state_machine.desk.current_player.privileges = 1
        state_machine.desk.current_player.reserved = []
        
        current_action = state_machine.get_current_action()
        
        assert current_action.state == GameState.START_OF_ROUND
        assert "Choose your action" in current_action.explanation
        assert len(current_action.buttons) > 0
        
        # Check that privilege button is available
        button_actions = [btn.action for btn in current_action.buttons]
        assert "use_privilege" in button_actions
    
    def test_get_current_action_use_privilege(self, state_machine):
        """Test getting current action for USE_PRIVILEGE state."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        current_action = state_machine.get_current_action()
        
        assert current_action.state == GameState.USE_PRIVILEGE
        assert "Select a token" in current_action.explanation
        
        # Check buttons
        button_actions = [btn.action for btn in current_action.buttons]
        assert "confirm" in button_actions
        assert "cancel" in button_actions
        
        # Confirm button should be disabled initially
        confirm_button = next(btn for btn in current_action.buttons if btn.action == "confirm")
        assert not confirm_button.enabled
    
    def test_get_current_action_with_selection(self, state_machine):
        """Test getting current action when elements are selected."""
        state_machine.current_state = GameState.USE_PRIVILEGE
        
        # Add a selection
        mock_element = Mock()
        state_machine.current_selection = [mock_element]
        
        current_action = state_machine.get_current_action()
        
        # Confirm button should now be enabled
        confirm_button = next(btn for btn in current_action.buttons if btn.action == "confirm")
        assert confirm_button.enabled
    
    def test_get_current_action_take_tokens(self, state_machine):
        """Test getting current action for TAKE_TOKENS state."""
        state_machine.current_state = GameState.TAKE_TOKENS
        
        current_action = state_machine.get_current_action()
        
        assert current_action.state == GameState.TAKE_TOKENS
        assert "Select up to 3" in current_action.explanation
        
        button_actions = [btn.action for btn in current_action.buttons]
        assert "confirm" in button_actions
        assert "cancel" in button_actions
    
    def test_get_current_action_all_states(self, state_machine):
        """Test getting current action for all valid game states."""
        # Test that all states return valid CurrentAction objects
        for state in GameState:
            current_action = state_machine.get_current_action(state)
            assert isinstance(current_action, CurrentAction)
            assert current_action.state == state
            assert isinstance(current_action.explanation, str)
            assert isinstance(current_action.buttons, list) 