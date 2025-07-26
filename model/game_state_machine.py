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
        GameState.USE_PRIVILEGE: SelectionRules(["Token"], 1, 1),
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


class GameStateMachine:
    def __init__(self, desk):
        self.desk = desk
        self.current_state = GameState.START_OF_ROUND
        self.current_selection = []  # Now stores LayoutElement objects directly

    def get_selection_rules(self, state: GameState = None) -> SelectionRules:
        """Get selection rules for the current or specified state."""
        state = state or self.current_state
        return GameStateConfig.get_selection_rules(state)

    def can_select_element(self, layout_element, element_type_name: str = None) -> Tuple[bool, str]:
        """
        Check if an element can be selected in the current state.
        Returns (can_select, reason_if_not)
        """
        if element_type_name is None:
            element_type_name = type(layout_element.element).__name__
        
        rules = self.get_selection_rules()
        
        # Check if type is allowed
        if not rules.can_select_type(element_type_name):
            return False, f"Cannot select {element_type_name} in {self.current_state.value}"
        
        # Check if we can select more
        if not rules.can_select_more(len(self.current_selection)):
            return False, f"Cannot select more than {rules.max_selections} elements"
        
        # Check special rules
        if rules.special_rules:
            if element_type_name == "Token":
                if rules.special_rules.get("no_gold") and hasattr(layout_element.element, 'color') and layout_element.element.color == "gold":
                    return False, "Cannot select gold tokens in this state"
                if rules.special_rules.get("require_gold") and len(self.current_selection) == 0:
                    if not (hasattr(layout_element.element, 'color') and layout_element.element.color == "gold"):
                        return False, "Must select gold token first"
        
        return True, ""

    def select_element(self, layout_element, element_type_name: str = None) -> Tuple[bool, str]:
        """
        Attempt to select an element. Returns (success, message)
        """
        if layout_element in self.current_selection:
            self.current_selection.remove(layout_element)
            return True, f"Deselected {element_type_name or type(layout_element.element).__name__}"
        
        can_select, reason = self.can_select_element(layout_element, element_type_name)
        if can_select:
            self.current_selection.append(layout_element)
            return True, f"Selected {element_type_name or type(layout_element.element).__name__}"
        else:
            return False, reason

    def can_confirm_selection(self) -> Tuple[bool, str]:
        """Check if current selection can be confirmed."""
        rules = self.get_selection_rules()
        
        if not rules.has_minimum_selections(len(self.current_selection)):
            return False, f"Must select at least {rules.min_selections} elements"
        
        # Add any state-specific validation here
        if self.current_state == GameState.TAKE_TOKENS:
            # Check if tokens form a valid combination using existing game logic
            if not self._validate_token_line():
                return False, "Selected tokens do not form a valid combination (must be adjacent in a straight line)"
        
        return True, ""

    def _build_combo_from_selection(self) -> Tuple[Optional[Dict], str]:
        """
        Build a token combo from current selection.
        Returns (combo_dict, error_message). If combo_dict is None, error_message explains why.
        """
        if not self.current_selection:
            return None, "No tokens selected"
            
        combo = {}
        for layout_element in self.current_selection:
            token = layout_element.element
            position = layout_element.metadata.get("position")
            if position is None:
                return None, "Invalid token selection - missing position data"
            
            if token not in combo:
                combo[token] = []
            combo[token].append(position)
        
        return combo, ""

    def _validate_token_line(self) -> bool:
        """Validate that selected tokens form a valid combination using existing game logic."""
        if len(self.current_selection) <= 1:
            return True
            
        combo, error = self._build_combo_from_selection()
        if combo is None:
            return False  # Invalid selection
        
        # Use the existing validation logic from the board
        eligible_draws = self.desk.board.eligible_draws()
        return combo in eligible_draws

    def handle_button_click(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """
        Handle button clicks and state transitions.
        Returns (action_to_execute, message)
        """
        match self.current_state:
            case GameState.START_OF_ROUND:
                return self._handle_start_of_round_buttons(button)
                
            case GameState.USE_PRIVILEGE:
                return self._handle_use_privilege_buttons(button)
                
            case GameState.REPLENISH_BOARD:
                return self._handle_replenish_board_buttons(button)
                
            case GameState.CHOOSE_MANDATORY_ACTION:
                return self._handle_choose_mandatory_action_buttons(button)
                
            case GameState.PURCHASE_CARD:
                return self._handle_purchase_card_buttons(button)
                
            case GameState.TAKE_TOKENS:
                return self._handle_take_tokens_buttons(button)
                
            case GameState.TAKE_GOLD_AND_RESERVE:
                return self._handle_take_gold_and_reserve_buttons(button)
                
            case GameState.POST_ACTION_CHECKS:
                return self._handle_post_action_checks_buttons(button)
                
            case GameState.CONFIRM_ROUND:
                return self._handle_confirm_round_buttons(button)
        
        return None, "Unknown state or button"

    def _handle_start_of_round_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in START_OF_ROUND state."""
        match button.action:
            case "use_privilege":
                self.transition_to(GameState.USE_PRIVILEGE)
                return None, "Select a token to take using privilege"
            case "replenish_board":
                self.transition_to(GameState.REPLENISH_BOARD)
                return None, "Confirm board replenishment"
            case "purchase_card":
                self.transition_to(GameState.PURCHASE_CARD)
                return None, "Select a card to purchase"
            case "take_tokens":
                self.transition_to(GameState.TAKE_TOKENS)
                return None, "Select tokens to take"
            case "take_gold_and_reserve":
                self.transition_to(GameState.TAKE_GOLD_AND_RESERVE)
                return None, "Select gold token and card to reserve"
        return None, f"Unknown action: {button.action}"

    def _handle_use_privilege_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in USE_PRIVILEGE state."""
        match button.action:
            case "cancel":
                self.transition_to(GameState.START_OF_ROUND)
                return None, "Cancelled privilege use"
            case "confirm":
                can_confirm, reason = self.can_confirm_selection()
                if not can_confirm:
                    return None, reason
                
                # Create the action
                selected_element = self.current_selection[0]
                action = Action(ActionType.USE_PRIVILEGE, {
                    "token": selected_element.element,
                    "position": selected_element.metadata["position"]
                })
                
                self.transition_to(GameState.START_OF_ROUND)
                return action, "Privilege used successfully"
        return None, f"Unknown action: {button.action}"

    def _handle_replenish_board_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in REPLENISH_BOARD state."""
        match button.action:
            case "confirm_replenish":
                action = Action(ActionType.REPLENISH_BOARD, {})
                self.transition_to(GameState.CHOOSE_MANDATORY_ACTION)
                return action, "Board replenished - choose mandatory action"
            case "cancel":
                self.transition_to(GameState.START_OF_ROUND)
                return None, "Cancelled board replenishment"
        return None, f"Unknown action: {button.action}"

    def _handle_choose_mandatory_action_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in CHOOSE_MANDATORY_ACTION state."""
        match button.action:
            case "purchase_card":
                self.transition_to(GameState.PURCHASE_CARD)
                return None, "Select a card to purchase"
            case "take_tokens":
                self.transition_to(GameState.TAKE_TOKENS)
                return None, "Select tokens to take"
            case "take_gold_and_reserve":
                self.transition_to(GameState.TAKE_GOLD_AND_RESERVE)
                return None, "Select gold token and card to reserve"
        return None, f"Unknown action: {button.action}"

    def _handle_purchase_card_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in PURCHASE_CARD state."""
        match button.action:
            case "cancel":
                self.transition_to(GameState.START_OF_ROUND)
                return None, "Cancelled card purchase"
            case "confirm":
                can_confirm, reason = self.can_confirm_selection()
                if not can_confirm:
                    return None, reason
                
                selected_element = self.current_selection[0]
                selected_card = selected_element.element
                
                if not self.desk.current_player.can_afford(selected_card):
                    return None, "Cannot afford this card"
                
                action = Action(ActionType.PURCHASE_CARD, {
                    "card": selected_card,
                    "level": selected_element.metadata["level"],
                    "index": selected_element.metadata["index"]
                })
                
                self.transition_to(GameState.POST_ACTION_CHECKS)
                return action, "Card purchased successfully"
        return None, f"Unknown action: {button.action}"

    def _handle_take_tokens_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in TAKE_TOKENS state."""
        match button.action:
            case "cancel":
                self.transition_to(GameState.START_OF_ROUND)
                return None, "Cancelled token taking"
            case "confirm":
                can_confirm, reason = self.can_confirm_selection()
                if not can_confirm:
                    return None, reason
                
                # Build combo using the helper method
                combo, error = self._build_combo_from_selection()
                if combo is None:
                    return None, error
                
                # The validation is already done in can_confirm_selection via _validate_token_line
                # So we can directly create the action
                action = Action(ActionType.TAKE_TOKENS, {"combo": combo})
                self.transition_to(GameState.POST_ACTION_CHECKS)
                return action, "Tokens taken successfully"
        return None, f"Unknown action: {button.action}"

    def _handle_take_gold_and_reserve_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in TAKE_GOLD_AND_RESERVE state."""
        match button.action:
            case "cancel":
                self.transition_to(GameState.START_OF_ROUND)
                return None, "Cancelled gold and reserve action"
            case "confirm":
                # TODO: Implement gold and reserve logic
                # You'll need to validate that one gold token and one card are selected
                return None, "Gold and reserve action not yet implemented"
        return None, f"Unknown action: {button.action}"

    def _handle_post_action_checks_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in POST_ACTION_CHECKS state."""
        match button.action:
            case "continue_to_confirm_round":
                self.transition_to(GameState.CONFIRM_ROUND)
                return None, "Ready to confirm round"
        return None, f"Unknown action: {button.action}"

    def _handle_confirm_round_buttons(self, button: ActionButton) -> Tuple[Optional[Action], str]:
        """Handle buttons in CONFIRM_ROUND state."""
        match button.action:
            case "finish_round":
                self.desk.next_player()
                self.transition_to(GameState.START_OF_ROUND)
                return None, "Round finished - next player's turn"
            case "rollback_to_start":
                # The controller will handle the actual rollback
                self.transition_to(GameState.START_OF_ROUND)
                return None, "Rolled back to start of round"
        return None, f"Unknown action: {button.action}"

    def transition_to(self, new_state: GameState):
        """Transition to a new state and clear selections if needed."""
        old_state = self.current_state
        self.current_state = new_state
        
        # Clear selections when transitioning to states that don't allow them
        new_rules = self.get_selection_rules(new_state)
        if not new_rules.allowed_types:
            self.current_selection.clear()

    def get_current_action(self, state: GameState = None) -> CurrentAction:
        """Get current action with enhanced state information."""
        state = state or self.current_state
        player = self.desk.current_player
        rules = self.get_selection_rules(state)
        
        match state:
            case GameState.START_OF_ROUND:
                buttons = []
                explanation = "Choose your action:"
                
                # Optional actions first
                if player.privileges > 0:
                    buttons.append(ActionButton("Use Privilege", "use_privilege"))
                if not self.desk.bag.is_empty():
                    buttons.append(ActionButton("Replenish Board", "replenish_board"))
                
                # Mandatory actions
                buttons.append(ActionButton("Purchase a Card", "purchase_card"))
                buttons.append(ActionButton("Take Tokens", "take_tokens"))
                # Fix: use Token("gold") instead of "gold" string
                gold_count = sum(count for token, count in self.desk.board.counts().items() if token.color == "gold")
                if gold_count > 0 and len(player.reserved) < 3:
                    buttons.append(ActionButton("Take Gold & Reserve", "take_gold_and_reserve"))
                
                return CurrentAction(state, explanation, buttons)
                
            case GameState.USE_PRIVILEGE:
                explanation = f"Select a token to take (max {rules.max_selections}):"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(self.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(state, explanation, buttons)
                
            case GameState.REPLENISH_BOARD:
                explanation = "Replenish the board? (Opponent gains privilege)"
                buttons = [
                    ActionButton("Confirm", "confirm_replenish"),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(state, explanation, buttons)
                
            case GameState.CHOOSE_MANDATORY_ACTION:
                explanation = "Choose a mandatory action:"
                buttons = [
                    ActionButton("Purchase a Card", "purchase_card"),
                    ActionButton("Take Tokens", "take_tokens"),
                    ActionButton("Take Gold & Reserve", "take_gold_and_reserve")
                ]
                return CurrentAction(state, explanation, buttons)
                
            case GameState.PURCHASE_CARD:
                explanation = f"Select a card to purchase (max {rules.max_selections}):"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(self.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(state, explanation, buttons)
                
            case GameState.TAKE_TOKENS:
                explanation = f"Select up to {rules.max_selections} eligible tokens:"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(self.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(state, explanation, buttons)
                
            case GameState.TAKE_GOLD_AND_RESERVE:
                explanation = "Select gold token and card to reserve:"
                buttons = [
                    ActionButton("Confirm", "confirm", enabled=rules.has_minimum_selections(len(self.current_selection))),
                    ActionButton("Cancel", "cancel")
                ]
                return CurrentAction(state, explanation, buttons)
                
            case GameState.POST_ACTION_CHECKS:
                explanation = "Action completed. Checking for discard and victory..."
                buttons = [
                    ActionButton("Continue", "continue_to_confirm_round")
                ]
                return CurrentAction(state, explanation, buttons)
                
            case GameState.CONFIRM_ROUND:
                explanation = "Finish this round?"
                buttons = [
                    ActionButton("Yes", "finish_round"),
                    ActionButton("No", "rollback_to_start")
                ]
                return CurrentAction(state, explanation, buttons)
                
        return CurrentAction(state, "Unknown state", []) 