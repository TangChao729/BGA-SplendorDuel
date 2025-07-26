from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from model.tokens import Token
    from model.cards import Card

from model.actions import ActionType, Action, ActionButton


class GameState(Enum):
    """Enumeration of all possible game states."""
    START_OF_ROUND = "start_of_round"
    USE_PRIVILEGE = "use_privilege"
    REPLENISH_BOARD = "replenish_board"
    CHOOSE_MANDATORY_ACTION = "choose_mandatory_action"
    PURCHASE_CARD = "purchase_card"
    TAKE_TOKENS = "take_tokens"
    TAKE_GOLD_AND_RESERVE = "take_gold_and_reserve"
    POST_ACTION_CHECKS = "post_action_checks"
    CONFIRM_ROUND = "confirm_round"


@dataclass
class SelectionRules:
    """Rules for element selection in a given state."""
    allowed_types: List[str]
    max_selections: int
    min_selections: int = 0
    special_rules: Optional[Dict[str, Any]] = None
    
    def can_select_type(self, element_type_name: str) -> bool:
        return element_type_name in self.allowed_types
    
    def can_select_more(self, current_count: int) -> bool:
        return current_count < self.max_selections
    
    def has_minimum_selections(self, current_count: int) -> bool:
        return current_count >= self.min_selections


class GameStateConfig:
    """Configuration for game states and their selection rules."""
    
    SELECTION_RULES = {
        GameState.START_OF_ROUND: SelectionRules([], 0),
        GameState.USE_PRIVILEGE: SelectionRules(["Token"], 1, 1, {"no_gold": True}),
        GameState.REPLENISH_BOARD: SelectionRules([], 0),
        GameState.CHOOSE_MANDATORY_ACTION: SelectionRules([], 0),
        GameState.PURCHASE_CARD: SelectionRules(["Card"], 1, 1),
        GameState.TAKE_TOKENS: SelectionRules(["Token"], 3, 1, {"no_gold": True}),
        GameState.TAKE_GOLD_AND_RESERVE: SelectionRules(["Token", "Card"], 2, 2, {"require_gold": True}),
        GameState.POST_ACTION_CHECKS: SelectionRules([], 0),
        GameState.CONFIRM_ROUND: SelectionRules([], 0),
    }
    
    @classmethod
    def get_selection_rules(cls, state: GameState) -> SelectionRules:
        return cls.SELECTION_RULES.get(state, SelectionRules([], 0))
    
    @classmethod
    def can_select_element(cls, state: GameState, element_type_name: str, current_count: int) -> bool:
        rules = cls.get_selection_rules(state)
        return rules.can_select_type(element_type_name) and rules.can_select_more(current_count)


@dataclass
class CurrentAction:
    """Represents the current game state and available actions."""
    state: GameState
    explanation: str
    buttons: List[ActionButton]
    
    def __post_init__(self):
        if not isinstance(self.state, GameState):
            self.state = GameState(self.state)


@dataclass
class GameSessionState:
    """Immutable state object representing the current game session UI state."""
    current_state: GameState
    current_selection: List[Any]  # LayoutElement objects
    
    def with_state(self, new_state: GameState) -> 'GameSessionState':
        """Return a new session state with updated game state."""
        return GameSessionState(new_state, self.current_selection.copy())
    
    def with_selection(self, new_selection: List[Any]) -> 'GameSessionState':
        """Return a new session state with updated selection."""
        return GameSessionState(self.current_state, new_selection.copy())
    
    def with_state_and_selection(self, new_state: GameState, new_selection: List[Any]) -> 'GameSessionState':
        """Return a new session state with both state and selection updated."""
        return GameSessionState(new_state, new_selection.copy())


class GameStateManager:
    """Stateless game state management functions."""
    
    @staticmethod
    def get_selection_rules(state: GameState) -> SelectionRules:
        """Get selection rules for the given state."""
        return GameStateConfig.get_selection_rules(state)
    
    @staticmethod
    def can_select_element(
        session: GameSessionState,
        layout_element: Any,
        desk: Any,
        element_type_name: str = None
    ) -> Tuple[bool, str]:
        """
        Check if an element can be selected in the current state.
        Returns (can_select, reason_if_not)
        """
        if element_type_name is None:
            element_type_name = type(layout_element.element).__name__
        
        rules = GameStateManager.get_selection_rules(session.current_state)
        
        # Check if type is allowed
        if not rules.can_select_type(element_type_name):
            return False, f"Cannot select {element_type_name} in {session.current_state.value}"
        
        # Check if we can select more
        if not rules.can_select_more(len(session.current_selection)):
            return False, f"Cannot select more than {rules.max_selections} elements"
        
        # Check special rules
        if rules.special_rules:
            if element_type_name == "Token":
                if rules.special_rules.get("no_gold") and hasattr(layout_element.element, 'color') and layout_element.element.color == "gold":
                    return False, "Cannot select gold tokens in this state"
                if rules.special_rules.get("require_gold") and len(session.current_selection) == 0:
                    if not (hasattr(layout_element.element, 'color') and layout_element.element.color == "gold"):
                        return False, "Must select gold token first"
        
        return True, ""
    
    @staticmethod
    def select_element(
        session: GameSessionState,
        layout_element: Any,
        desk: Any,
        element_type_name: str = None
    ) -> Tuple[GameSessionState, bool, str]:
        """
        Attempt to select an element. Returns (new_session, success, message)
        """
        # Check if element is already selected
        if layout_element in session.current_selection:
            new_selection = [elem for elem in session.current_selection if elem != layout_element]
            new_session = session.with_selection(new_selection)
            element_name = element_type_name or type(layout_element.element).__name__
            return new_session, True, f"Deselected {element_name}"
        
        # Check if we can select this element
        can_select, reason = GameStateManager.can_select_element(session, layout_element, desk, element_type_name)
        if can_select:
            new_selection = session.current_selection + [layout_element]
            new_session = session.with_selection(new_selection)
            element_name = element_type_name or type(layout_element.element).__name__
            return new_session, True, f"Selected {element_name}"
        else:
            return session, False, reason
    
    @staticmethod
    def can_confirm_selection(session: GameSessionState, desk: Any) -> Tuple[bool, str]:
        """Check if current selection can be confirmed."""
        rules = GameStateManager.get_selection_rules(session.current_state)
        
        if not rules.has_minimum_selections(len(session.current_selection)):
            return False, f"Must select at least {rules.min_selections} elements"
        
        # Add any state-specific validation here
        if session.current_state == GameState.TAKE_TOKENS:
            # Check if tokens form a valid combination using existing game logic
            if not GameStateManager._validate_token_line(session, desk):
                return False, "Selected tokens do not form a valid combination (must be adjacent in a straight line)"
        
        return True, ""
    
    @staticmethod
    def _build_combo_from_selection(session: GameSessionState) -> Tuple[Optional[Dict], str]:
        """
        Build a token combo from current selection.
        Returns (combo_dict, error_message). If combo_dict is None, error_message explains why.
        """
        if not session.current_selection:
            return None, "No tokens selected"
            
        combo = {}
        for layout_element in session.current_selection:
            token = layout_element.element
            position = layout_element.metadata.get("position")
            if position is None:
                return None, "Invalid token selection - missing position data"
            
            if token not in combo:
                combo[token] = []
            combo[token].append(position)
        
        return combo, ""
    
    @staticmethod
    def _validate_token_line(session: GameSessionState, desk: Any) -> bool:
        """Validate that selected tokens form a valid combination using existing game logic."""
        if len(session.current_selection) <= 1:
            return True
            
        combo, error = GameStateManager._build_combo_from_selection(session)
        if combo is None:
            return False  # Invalid selection
        
        # Use the existing validation logic from the board
        eligible_draws = desk.board.eligible_draws()
        return combo in eligible_draws
    
    @staticmethod
    def handle_button_click(
        session: GameSessionState,
        button: ActionButton,
        desk: Any
    ) -> Tuple[GameSessionState, Optional[Action], str]:
        """
        Handle button clicks and state transitions.
        Returns (new_session, action_to_execute, message)
        """
        match session.current_state:
            case GameState.START_OF_ROUND:
                return GameStateManager._handle_start_of_round_buttons(session, button, desk)
                
            case GameState.USE_PRIVILEGE:
                return GameStateManager._handle_use_privilege_buttons(session, button, desk)
                
            case GameState.REPLENISH_BOARD:
                return GameStateManager._handle_replenish_board_buttons(session, button, desk)
                
            case GameState.CHOOSE_MANDATORY_ACTION:
                return GameStateManager._handle_choose_mandatory_action_buttons(session, button, desk)
                
            case GameState.PURCHASE_CARD:
                return GameStateManager._handle_purchase_card_buttons(session, button, desk)
                
            case GameState.TAKE_TOKENS:
                return GameStateManager._handle_take_tokens_buttons(session, button, desk)
                
            case GameState.TAKE_GOLD_AND_RESERVE:
                return GameStateManager._handle_take_gold_and_reserve_buttons(session, button, desk)
                
            case GameState.POST_ACTION_CHECKS:
                return GameStateManager._handle_post_action_checks_buttons(session, button, desk)
                
            case GameState.CONFIRM_ROUND:
                return GameStateManager._handle_confirm_round_buttons(session, button, desk)
        
        return session, None, "Unknown state or button"
    
    @staticmethod
    def _handle_start_of_round_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in START_OF_ROUND state."""
        match button.action:
            case "use_privilege":
                new_session = session.with_state_and_selection(GameState.USE_PRIVILEGE, [])
                return new_session, None, "Select a token to take using privilege"
            case "replenish_board":
                new_session = session.with_state(GameState.REPLENISH_BOARD)
                return new_session, None, "Confirm board replenishment"
            case "purchase_card":
                new_session = session.with_state_and_selection(GameState.PURCHASE_CARD, [])
                return new_session, None, "Select a card to purchase"
            case "take_tokens":
                new_session = session.with_state_and_selection(GameState.TAKE_TOKENS, [])
                return new_session, None, "Select tokens to take"
            case "take_gold_and_reserve":
                new_session = session.with_state_and_selection(GameState.TAKE_GOLD_AND_RESERVE, [])
                return new_session, None, "Select gold token and card to reserve"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_use_privilege_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in USE_PRIVILEGE state."""
        match button.action:
            case "cancel":
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, None, "Cancelled privilege use"
            case "confirm":
                can_confirm, reason = GameStateManager.can_confirm_selection(session, desk)
                if not can_confirm:
                    return session, None, reason
                
                # Create the action
                selected_element = session.current_selection[0]
                action = Action(ActionType.USE_PRIVILEGE, {
                    "token": selected_element.element,
                    "position": selected_element.metadata["position"]
                })
                
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, action, "Privilege used successfully"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_replenish_board_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in REPLENISH_BOARD state."""
        match button.action:
            case "confirm_replenish":
                action = Action(ActionType.REPLENISH_BOARD, {})
                new_session = session.with_state(GameState.CHOOSE_MANDATORY_ACTION)
                return new_session, action, "Board replenished - choose mandatory action"
            case "cancel":
                new_session = session.with_state(GameState.START_OF_ROUND)
                return new_session, None, "Cancelled board replenishment"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_choose_mandatory_action_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in CHOOSE_MANDATORY_ACTION state."""
        match button.action:
            case "purchase_card":
                new_session = session.with_state_and_selection(GameState.PURCHASE_CARD, [])
                return new_session, None, "Select a card to purchase"
            case "take_tokens":
                new_session = session.with_state_and_selection(GameState.TAKE_TOKENS, [])
                return new_session, None, "Select tokens to take"
            case "take_gold_and_reserve":
                new_session = session.with_state_and_selection(GameState.TAKE_GOLD_AND_RESERVE, [])
                return new_session, None, "Select gold token and card to reserve"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_purchase_card_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in PURCHASE_CARD state."""
        match button.action:
            case "cancel":
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, None, "Cancelled card purchase"
            case "confirm":
                can_confirm, reason = GameStateManager.can_confirm_selection(session, desk)
                if not can_confirm:
                    return session, None, reason
                
                selected_element = session.current_selection[0]
                selected_card = selected_element.element
                
                if not desk.current_player.can_afford(selected_card):
                    return session, None, "Cannot afford this card"
                
                action = Action(ActionType.PURCHASE_CARD, {
                    "card": selected_card,
                    "level": selected_element.metadata["level"],
                    "index": selected_element.metadata["index"]
                })
                
                new_session = session.with_state_and_selection(GameState.POST_ACTION_CHECKS, [])
                return new_session, action, "Card purchased successfully"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_take_tokens_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in TAKE_TOKENS state."""
        match button.action:
            case "cancel":
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, None, "Cancelled token taking"
            case "confirm":
                can_confirm, reason = GameStateManager.can_confirm_selection(session, desk)
                if not can_confirm:
                    return session, None, reason
                
                # Build combo using the helper method
                combo, error = GameStateManager._build_combo_from_selection(session)
                if combo is None:
                    return session, None, error
                
                # The validation is already done in can_confirm_selection via _validate_token_line
                # So we can directly create the action
                action = Action(ActionType.TAKE_TOKENS, {"combo": combo})
                new_session = session.with_state_and_selection(GameState.POST_ACTION_CHECKS, [])
                return new_session, action, "Tokens taken successfully"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_take_gold_and_reserve_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in TAKE_GOLD_AND_RESERVE state."""
        match button.action:
            case "cancel":
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, None, "Cancelled gold and reserve action"
            case "confirm":
                # TODO: Implement gold and reserve logic
                # You'll need to validate that one gold token and one card are selected
                return session, None, "Gold and reserve action not yet implemented"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_post_action_checks_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in POST_ACTION_CHECKS state."""
        match button.action:
            case "continue_to_confirm_round":
                new_session = session.with_state(GameState.CONFIRM_ROUND)
                return new_session, None, "Ready to confirm round"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_confirm_round_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in CONFIRM_ROUND state."""
        match button.action:
            case "finish_round":
                desk.next_player()
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, None, "Round finished - next player's turn"
            case "rollback_to_start":
                # The controller will handle the actual rollback
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, None, "Rolled back to start of round"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def get_current_action(session: GameSessionState, desk: Any) -> CurrentAction:
        """Get current action with enhanced state information."""
        player = desk.current_player
        rules = GameStateManager.get_selection_rules(session.current_state)
        
        match session.current_state:
            case GameState.START_OF_ROUND:
                buttons = []
                explanation = "Choose your action:"
                
                # Optional actions first
                if player.privileges > 0:
                    buttons.append(ActionButton("Use Privilege", "use_privilege"))
                if not desk.bag.is_empty():
                    buttons.append(ActionButton("Replenish Board", "replenish_board"))
                
                # Mandatory actions
                buttons.append(ActionButton("Purchase a Card", "purchase_card"))
                buttons.append(ActionButton("Take Tokens", "take_tokens"))
                # Fix: use Token("gold") instead of "gold" string
                gold_count = sum(count for token, count in desk.board.counts().items() if token.color == "gold")
                if gold_count > 0 and len(player.reserved) < 3:
                    buttons.append(ActionButton("Take Gold & Reserve", "take_gold_and_reserve"))
                
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.USE_PRIVILEGE:
                explanation = f"Select a token to take (max {rules.max_selections}):"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(session.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.REPLENISH_BOARD:
                explanation = "Replenish the board? (Opponent gains privilege)"
                buttons = [
                    ActionButton("Confirm", "confirm_replenish"),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.CHOOSE_MANDATORY_ACTION:
                explanation = "Choose a mandatory action:"
                buttons = [
                    ActionButton("Purchase a Card", "purchase_card"),
                    ActionButton("Take Tokens", "take_tokens"),
                    ActionButton("Take Gold & Reserve", "take_gold_and_reserve")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.PURCHASE_CARD:
                explanation = f"Select a card to purchase (max {rules.max_selections}):"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(session.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.TAKE_TOKENS:
                explanation = f"Select up to {rules.max_selections} eligible tokens:"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(session.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.TAKE_GOLD_AND_RESERVE:
                explanation = "Select gold token and card to reserve:"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(session.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.POST_ACTION_CHECKS:
                explanation = "Action completed. Checking for discard and victory..."
                buttons = [
                    ActionButton("Continue", "continue_to_confirm_round")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.CONFIRM_ROUND:
                explanation = "Finish this round?"
                buttons = [
                    ActionButton("Yes", "finish_round"),
                    ActionButton("No", "rollback_to_start")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
        return CurrentAction(session.current_state, "Unknown state", []) 