import pytest
from unittest.mock import Mock, MagicMock
from model.game_state_machine import (
    GameState, SelectionRules, GameStateConfig, CurrentAction, GameSessionState, GameStateManager
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
    """Test the SelectionRules dataclass."""
    
    def test_selection_rules_creation(self):
        """Test creating selection rules."""
        rules = SelectionRules(["Token"], 3, 1)
        assert rules.allowed_types == ["Token"]
        assert rules.max_selections == 3
        assert rules.min_selections == 1
        assert rules.special_rules is None
    
    def test_selection_rules_with_special_rules(self):
        """Test creating selection rules with special rules."""
        special = {"no_gold": True}
        rules = SelectionRules(["Token"], 3, 1, special)
        assert rules.special_rules == special
    
    def test_can_select_type(self):
        """Test type checking in selection rules."""
        rules = SelectionRules(["Token", "Card"], 2)
        assert rules.can_select_type("Token")
        assert rules.can_select_type("Card")
        assert not rules.can_select_type("Invalid")
    
    def test_can_select_more(self):
        """Test count checking in selection rules."""
        rules = SelectionRules(["Token"], 3)
        assert rules.can_select_more(0)
        assert rules.can_select_more(2)
        assert not rules.can_select_more(3)
        assert not rules.can_select_more(4)
    
    def test_has_minimum_selections(self):
        """Test minimum selection checking."""
        rules = SelectionRules(["Token"], 3, 1)
        assert not rules.has_minimum_selections(0)
        assert rules.has_minimum_selections(1)
        assert rules.has_minimum_selections(2)


class TestGameStateConfig:
    """Test the GameStateConfig class."""
    
    def test_get_selection_rules_known_state(self):
        """Test getting selection rules for known states."""
        rules = GameStateConfig.get_selection_rules(GameState.USE_PRIVILEGE)
        assert isinstance(rules, SelectionRules)
        assert rules.allowed_types == ["Token"]
        assert rules.max_selections == 1
        assert rules.min_selections == 1
    
    def test_get_selection_rules_unknown_state(self):
        """Test getting selection rules for unknown state."""
        # This should return default rules
        rules = GameStateConfig.get_selection_rules("invalid_state")
        assert isinstance(rules, SelectionRules)
        assert rules.allowed_types == []
        assert rules.max_selections == 0
    
    def test_can_select_element_class_method(self):
        """Test the class method for element selection checking."""
        can_select = GameStateConfig.can_select_element(GameState.USE_PRIVILEGE, "Token", 0)
        assert can_select
        
        cannot_select = GameStateConfig.can_select_element(GameState.USE_PRIVILEGE, "Token", 1)
        assert not cannot_select


class TestCurrentAction:
    """Test the CurrentAction dataclass."""
    
    def test_current_action_creation(self):
        """Test creating a CurrentAction."""
        buttons = [ActionButton("Test", "test")]
        action = CurrentAction(GameState.START_OF_ROUND, "Test explanation", buttons)
        assert action.state == GameState.START_OF_ROUND
        assert action.explanation == "Test explanation"
        assert action.buttons == buttons
    
    def test_current_action_state_conversion(self):
        """Test that string states are converted to GameState enum."""
        action = CurrentAction("start_of_round", "Test", [])
        assert action.state == GameState.START_OF_ROUND


class TestGameSessionState:
    """Test the GameSessionState dataclass."""
    
    def test_creation(self):
        """Test creating a GameSessionState."""
        session = GameSessionState(GameState.START_OF_ROUND, [])
        assert session.current_state == GameState.START_OF_ROUND
        assert session.current_selection == []
    
    def test_with_state_immutability(self):
        """Test that with_state returns a new object."""
        original = GameSessionState(GameState.START_OF_ROUND, ["item"])
        new_session = original.with_state(GameState.USE_PRIVILEGE)
        
        # Original should be unchanged
        assert original.current_state == GameState.START_OF_ROUND
        assert original.current_selection == ["item"]
        
        # New session should have new state but same selection
        assert new_session.current_state == GameState.USE_PRIVILEGE
        assert new_session.current_selection == ["item"]
    
    def test_with_selection_immutability(self):
        """Test that with_selection returns a new object."""
        original = GameSessionState(GameState.START_OF_ROUND, ["item1"])
        new_session = original.with_selection(["item2", "item3"])
        
        # Original should be unchanged
        assert original.current_selection == ["item1"]
        
        # New session should have new selection but same state
        assert new_session.current_state == GameState.START_OF_ROUND
        assert new_session.current_selection == ["item2", "item3"]
    
    def test_with_state_and_selection_immutability(self):
        """Test that with_state_and_selection returns a new object."""
        original = GameSessionState(GameState.START_OF_ROUND, ["item1"])
        new_session = original.with_state_and_selection(GameState.USE_PRIVILEGE, ["item2"])
        
        # Original should be unchanged
        assert original.current_state == GameState.START_OF_ROUND
        assert original.current_selection == ["item1"]
        
        # New session should have both new state and selection
        assert new_session.current_state == GameState.USE_PRIVILEGE
        assert new_session.current_selection == ["item2"]


class TestGameStateManager:
    """Test the stateless GameStateManager class."""
    
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
    def session_state(self):
        """Create a GameSessionState for testing."""
        return GameSessionState(GameState.START_OF_ROUND, [])
    
    def test_get_selection_rules(self):
        """Test getting selection rules."""
        # Test getting rules for specific state
        rules = GameStateManager.get_selection_rules(GameState.USE_PRIVILEGE)
        assert isinstance(rules, SelectionRules)
        assert rules.allowed_types == ["Token"]
        assert rules.max_selections == 1
        
        # Test different state
        rules = GameStateManager.get_selection_rules(GameState.PURCHASE_CARD)
        assert rules.allowed_types == ["Card"]
        assert rules.max_selections == 1
    
    def test_can_select_element_basic(self, mock_desk, session_state):
        """Test basic element selection validation."""
        # Create session state that allows token selection
        session = GameSessionState(GameState.USE_PRIVILEGE, [])
        
        # Mock layout element
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        
        can_select, reason = GameStateManager.can_select_element(session, layout_element, mock_desk, "Token")
        assert can_select
        assert reason == ""
    
    def test_session_state_immutability(self, session_state):
        """Test that session state is immutable."""
        original_state = session_state.current_state
        original_selection_count = len(session_state.current_selection)
        
        # Create new session with different state
        new_session = session_state.with_state(GameState.USE_PRIVILEGE)
        
        # Original should be unchanged
        assert session_state.current_state == original_state
        assert len(session_state.current_selection) == original_selection_count
        
        # New session should have new state
        assert new_session.current_state == GameState.USE_PRIVILEGE
        assert len(new_session.current_selection) == original_selection_count
    
    def test_select_element_returns_new_session(self, mock_desk, session_state):
        """Test that select_element returns a new session state."""
        session = GameSessionState(GameState.USE_PRIVILEGE, [])
        
        # Mock layout element
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        
        new_session, success, message = GameStateManager.select_element(session, layout_element, mock_desk, "Token")
        
        # Original session should be unchanged
        assert len(session.current_selection) == 0
        
        # New session should have the selection
        assert success
        assert len(new_session.current_selection) == 1
        assert layout_element in new_session.current_selection
    
    def test_get_current_action_basic(self, mock_desk):
        """Test getting current action."""
        session = GameSessionState(GameState.START_OF_ROUND, [])
        current_action = GameStateManager.get_current_action(session, mock_desk)
        
        assert isinstance(current_action, CurrentAction)
        assert current_action.state == GameState.START_OF_ROUND
        assert isinstance(current_action.explanation, str)
        assert isinstance(current_action.buttons, list)
        assert len(current_action.buttons) > 0  # Should have some buttons


class TestCardAbility2ndColor:
    """Test the CARD_ABILITY_2ND_COLOR state (TAKE 2ND SAME ability)."""
    
    @pytest.fixture
    def mock_desk_with_ability(self):
        """Create mock desk with pending_ability_card_color."""
        desk = Mock()
        desk.pending_ability_card_color = "BLACK"
        desk.current_player = Mock()
        desk.current_player.name = "Player 1"
        return desk
    
    def test_card_ability_2nd_color_selection_rules(self):
        """Test that selection rules exist for CARD_ABILITY_2ND_COLOR."""
        rules = GameStateConfig.get_selection_rules(GameState.CARD_ABILITY_2ND_COLOR)
        assert "Token" in rules.allowed_types
        assert rules.max_selections == 1
        assert rules.min_selections == 0  # Optional selection
        assert rules.special_rules.get("match_card_color") is True
    
    def test_can_select_matching_color_token(self, mock_desk_with_ability):
        """Test that player can select token matching card color."""
        session = GameSessionState(GameState.CARD_ABILITY_2ND_COLOR, [])
        
        # Mock a BLACK token on the board
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "black"
        layout_element.metadata = {"position": (2, 3)}  # Board token
        
        can_select, reason = GameStateManager.can_select_element(
            session, layout_element, mock_desk_with_ability, "Token"
        )
        assert can_select is True
        assert reason == ""
    
    def test_cannot_select_wrong_color_token(self, mock_desk_with_ability):
        """Test that player cannot select token of different color."""
        session = GameSessionState(GameState.CARD_ABILITY_2ND_COLOR, [])
        
        # Mock a RED token on the board (wrong color)
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        layout_element.metadata = {"position": (2, 3)}  # Board token
        
        can_select, reason = GameStateManager.can_select_element(
            session, layout_element, mock_desk_with_ability, "Token"
        )
        assert can_select is False
        assert "black" in reason.lower()
    
    def test_cannot_select_player_token(self, mock_desk_with_ability):
        """Test that player cannot select their own tokens (only board tokens)."""
        session = GameSessionState(GameState.CARD_ABILITY_2ND_COLOR, [])
        
        # Mock a player token (has "player" in metadata)
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "black"
        layout_element.metadata = {"player": "Player 1"}  # Player token, not board token
        
        can_select, reason = GameStateManager.can_select_element(
            session, layout_element, mock_desk_with_ability, "Token"
        )
        assert can_select is False
        assert "board" in reason.lower()
    
    def test_confirm_with_selection_creates_action(self, mock_desk_with_ability):
        """Test that confirming with a selection creates TAKE_ABILITY_TOKEN action."""
        # Create a selection
        layout_element = Mock()
        layout_element.element = Token("black")
        layout_element.metadata = {"position": (2, 3)}
        
        session = GameSessionState(GameState.CARD_ABILITY_2ND_COLOR, [layout_element])
        button = ActionButton("Confirm selection", "confirm_selection")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_with_ability
        )
        
        assert new_session.current_state == GameState.POST_ACTION_CHECKS
        assert action is not None
        assert action.type == ActionType.TAKE_ABILITY_TOKEN
        assert action.payload["token"] == layout_element.element
        assert action.payload["position"] == (2, 3)
        assert "black" in message.lower() or "token" in message.lower()
    
    def test_confirm_without_selection_skips(self, mock_desk_with_ability):
        """Test that confirming without selection skips (no action created)."""
        session = GameSessionState(GameState.CARD_ABILITY_2ND_COLOR, [])
        button = ActionButton("Confirm selection", "confirm_selection")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_with_ability
        )
        
        assert new_session.current_state == GameState.POST_ACTION_CHECKS
        assert action is None
        assert "skip" in message.lower()
    
    def test_get_current_action_shows_correct_ui(self, mock_desk_with_ability):
        """Test that get_current_action returns correct UI for this state."""
        session = GameSessionState(GameState.CARD_ABILITY_2ND_COLOR, [])
        
        current_action = GameStateManager.get_current_action(session, mock_desk_with_ability)
        
        assert current_action.state == GameState.CARD_ABILITY_2ND_COLOR
        assert "black" in current_action.explanation.lower()
        assert len(current_action.buttons) == 1
        assert current_action.buttons[0].action == "confirm_selection"
    
    def test_purchase_card_with_ability_transitions_to_2nd_color_state(self, mock_desk_with_ability):
        """Test that purchasing a card with TAKE 2ND SAME ability transitions to the correct state."""
        # Create mock card with TAKE 2ND SAME ability
        mock_card = Mock()
        mock_card.ability = "TAKE 2ND SAME"
        mock_card.color = "BLACK"
        
        # Create mock layout element for the card
        layout_element = Mock()
        layout_element.element = mock_card
        layout_element.metadata = {"level": 1, "index": 0}
        
        # Set up desk to allow purchase
        mock_desk_with_ability.current_player.can_afford = Mock(return_value=True)
        
        session = GameSessionState(GameState.PURCHASE_CARD, [layout_element])
        button = ActionButton("Confirm", "confirm")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_with_ability
        )
        
        # Should transition to CARD_ABILITY_2ND_COLOR state
        assert new_session.current_state == GameState.CARD_ABILITY_2ND_COLOR
        assert action is not None
        assert action.type == ActionType.PURCHASE_CARD
        # pending_ability_card_color should be set
        assert mock_desk_with_ability.pending_ability_card_color == "BLACK"


class TestCardAbilitySteal:
    """Test the CARD_ABILITY_STEAL state (STEAL ability)."""
    
    @pytest.fixture
    def mock_desk_for_steal(self):
        """Create mock desk for steal ability tests."""
        desk = Mock()
        desk.pending_steal_return_state = "POST_ACTION_CHECKS"
        desk.current_player = Mock()
        desk.current_player.name = "Player 1"
        # Mock opponent
        opponent = Mock()
        opponent.name = "Player 2"
        desk.players = [desk.current_player, opponent]
        return desk
    
    def test_card_ability_steal_selection_rules(self):
        """Test that selection rules exist for CARD_ABILITY_STEAL."""
        rules = GameStateConfig.get_selection_rules(GameState.CARD_ABILITY_STEAL)
        assert "Token" in rules.allowed_types
        assert rules.max_selections == 1
        assert rules.min_selections == 0  # Optional selection
        assert rules.special_rules.get("opponent_tokens_only") is True
        assert rules.special_rules.get("no_gold") is True
    
    def test_can_select_opponent_token(self, mock_desk_for_steal):
        """Test that player can select opponent's token (non-gold)."""
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [])
        
        # Mock an opponent's token
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        layout_element.metadata = {"player": "Player 2"}  # Opponent's token
        
        can_select, reason = GameStateManager.can_select_element(
            session, layout_element, mock_desk_for_steal, "Token"
        )
        assert can_select is True
        assert reason == ""
    
    def test_cannot_select_own_token(self, mock_desk_for_steal):
        """Test that player cannot select their own token."""
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [])
        
        # Mock current player's token
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        layout_element.metadata = {"player": "Player 1"}  # Current player's token
        
        can_select, reason = GameStateManager.can_select_element(
            session, layout_element, mock_desk_for_steal, "Token"
        )
        assert can_select is False
        assert "opponent" in reason.lower()
    
    def test_cannot_select_board_token(self, mock_desk_for_steal):
        """Test that player cannot select board tokens (only opponent's)."""
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [])
        
        # Mock a board token (no "player" in metadata)
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "red"
        layout_element.metadata = {"position": (2, 3)}  # Board token
        
        can_select, reason = GameStateManager.can_select_element(
            session, layout_element, mock_desk_for_steal, "Token"
        )
        assert can_select is False
        assert "opponent" in reason.lower()
    
    def test_cannot_select_gold_token(self, mock_desk_for_steal):
        """Test that player cannot steal gold tokens."""
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [])
        
        # Mock opponent's gold token
        layout_element = Mock()
        layout_element.element = Mock()
        layout_element.element.color = "gold"
        layout_element.metadata = {"player": "Player 2"}  # Opponent's token
        
        can_select, reason = GameStateManager.can_select_element(
            session, layout_element, mock_desk_for_steal, "Token"
        )
        assert can_select is False
        assert "gold" in reason.lower()
    
    def test_confirm_with_selection_creates_steal_action(self, mock_desk_for_steal):
        """Test that confirming with a selection creates STEAL_TOKEN action."""
        # Create a selection
        layout_element = Mock()
        layout_element.element = Token("red")
        layout_element.metadata = {"player": "Player 2"}
        
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [layout_element])
        button = ActionButton("Confirm selection", "confirm_selection")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_for_steal
        )
        
        assert new_session.current_state == GameState.POST_ACTION_CHECKS
        assert action is not None
        assert action.type == ActionType.STEAL_TOKEN
        assert action.payload["token"] == layout_element.element
        assert "stole" in message.lower() or "red" in message.lower()
    
    def test_confirm_without_selection_skips(self, mock_desk_for_steal):
        """Test that confirming without selection skips (no action created)."""
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [])
        button = ActionButton("Confirm selection", "confirm_selection")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_for_steal
        )
        
        assert new_session.current_state == GameState.POST_ACTION_CHECKS
        assert action is None
        assert "skip" in message.lower()
    
    def test_steal_from_royal_returns_to_check_discard(self, mock_desk_for_steal):
        """Test that stealing from royal returns to CHECK_DISCARD state."""
        mock_desk_for_steal.pending_steal_return_state = "CHECK_DISCARD"
        
        # Create a selection
        layout_element = Mock()
        layout_element.element = Token("blue")
        layout_element.metadata = {"player": "Player 2"}
        
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [layout_element])
        button = ActionButton("Confirm selection", "confirm_selection")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_for_steal
        )
        
        # Should return to CHECK_DISCARD since triggered from royal
        assert new_session.current_state == GameState.CHECK_DISCARD
        assert action is not None
        assert action.type == ActionType.STEAL_TOKEN
    
    def test_get_current_action_shows_correct_ui(self, mock_desk_for_steal):
        """Test that get_current_action returns correct UI for this state."""
        session = GameSessionState(GameState.CARD_ABILITY_STEAL, [])
        
        current_action = GameStateManager.get_current_action(session, mock_desk_for_steal)
        
        assert current_action.state == GameState.CARD_ABILITY_STEAL
        assert "opponent" in current_action.explanation.lower() or "steal" in current_action.explanation.lower()
        assert len(current_action.buttons) == 1
        assert current_action.buttons[0].action == "confirm_selection"
    
    def test_purchase_card_with_steal_ability_transitions_to_steal_state(self, mock_desk_for_steal):
        """Test that purchasing a card with STEAL ability transitions to the correct state."""
        # Create mock card with STEAL ability
        mock_card = Mock()
        mock_card.ability = "STEAL"
        mock_card.color = "BLACK"
        
        # Create mock layout element for the card
        layout_element = Mock()
        layout_element.element = mock_card
        layout_element.metadata = {"level": 2, "index": 0}
        
        # Set up desk to allow purchase
        mock_desk_for_steal.current_player.can_afford = Mock(return_value=True)
        
        session = GameSessionState(GameState.PURCHASE_CARD, [layout_element])
        button = ActionButton("Confirm", "confirm")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_for_steal
        )
        
        # Should transition to CARD_ABILITY_STEAL state
        assert new_session.current_state == GameState.CARD_ABILITY_STEAL
        assert action is not None
        assert action.type == ActionType.PURCHASE_CARD
        # pending_steal_return_state should be set to POST_ACTION_CHECKS
        assert mock_desk_for_steal.pending_steal_return_state == "POST_ACTION_CHECKS"
    
    def test_claim_royal_with_steal_ability_transitions_to_steal_state(self, mock_desk_for_steal):
        """Test that claiming a royal with STEAL ability transitions to the correct state."""
        # Create mock royal with STEAL ability
        mock_royal = Mock()
        mock_royal.ability = "STEAL"
        
        # Create mock layout element for the royal
        layout_element = Mock()
        layout_element.element = mock_royal
        layout_element.metadata = {"index": 0}
        
        session = GameSessionState(GameState.ROYAL_SELECTION, [layout_element])
        button = ActionButton("Confirm Royal", "confirm_royal")
        
        new_session, action, message = GameStateManager.handle_button_click(
            session, button, mock_desk_for_steal
        )
        
        # Should transition to CARD_ABILITY_STEAL state
        assert new_session.current_state == GameState.CARD_ABILITY_STEAL
        assert action is not None
        assert action.type == ActionType.CLAIM_ROYAL
        # pending_steal_return_state should be set to CHECK_DISCARD (from royal)
        assert mock_desk_for_steal.pending_steal_return_state == "CHECK_DISCARD" 