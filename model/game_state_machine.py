from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

# Use TYPE_CHECKING to avoid circular imports
# if TYPE_CHECKING:
from model.tokens import Token
from model.cards import Card, Deck
from model.element_reference import ElementReference
from model.actions import ActionType, Action, ActionButton


class GameState(Enum):
    """Enumeration of all possible game states."""
    # Main entry points
    START_OF_ROUND              = "start_of_round"          # DONE

    # Optional actions
    USE_PRIVILEGE               = "use_privilege"           # DONE
    REPLENISH_BOARD             = "replenish_board"         # TODO: After replenish or reserve face down cards, no going back to original state

    # Post optional actions 
    CHOOSE_MANDATORY_ACTION     = "choose_mandatory_action" # DONE

    # Mandatory actions
    PURCHASE_CARD               = "purchase_card"           # DONE
    TAKE_TOKENS                 = "take_tokens"             # DONE
    TAKE_GOLD_AND_RESERVE       = "take_gold_and_reserve"   # DONE

    # Post-action checks
    POST_ACTION_CHECKS          = "post_action_checks"      # DONE
    CHECK_DISCARD               = "check_discard"           # DONE
    DISCARD_TOKENS              = "discard_tokens"          # DONE
    ROYAL_SELECTION             = "royal_selection"         # DONE
    CARD_ABILITY_2ND_TURN       = "card_ability_2nd_turn"   # TODO
    CARD_ABILITY_JOKER          = "card_ability_joker"      # TODO
    CARD_ABILITY_2ND_COLOR      = "card_ability_2nd_color"  # DONE - TAKE 2ND SAME ability
    CARD_ABILITY_PRIVILEGE      = "card_ability_privilege"  # TODO
    CARD_ABILITY_STEAL          = "card_ability_steal"      # DONE - STEAL ability

    # End of round
    CONFIRM_ROUND               = "confirm_round"           # DONE
    
    # Game over
    GAME_OVER                   = "game_over"               # DONE - Victory achieved


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
        GameState.TAKE_GOLD_AND_RESERVE: SelectionRules(["Token", "Card", "Deck"], 2, 2, {"require_gold": True, "require_card": True}),
        GameState.POST_ACTION_CHECKS: SelectionRules([], 0),
        GameState.CHECK_DISCARD: SelectionRules([], 0),
        GameState.DISCARD_TOKENS: SelectionRules(["Token"], 10, 1, {"discard_mode": True, "player_tokens_only": True, "allow_partial": True}),
        GameState.ROYAL_SELECTION: SelectionRules(["Royal"], 1, 1),
        GameState.CONFIRM_ROUND: SelectionRules([], 0),
        GameState.CARD_ABILITY_2ND_COLOR: SelectionRules(["Token"], 1, 0, {"match_card_color": True, "board_tokens_only": True}),
        GameState.CARD_ABILITY_STEAL: SelectionRules(["Token"], 1, 0, {"opponent_tokens_only": True, "no_gold": True}),
        GameState.CARD_ABILITY_JOKER: SelectionRules(["BonusColor"], 1, 1, {"player_bonuses_only": True}),
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
    current_selection: List[ElementReference]
    
    def with_state(self, new_state: GameState) -> 'GameSessionState':
        """Return a new session state with updated game state."""
        return GameSessionState(new_state, self.current_selection.copy())
    
    def with_selection(self, new_selection: List[Any]) -> 'GameSessionState':
        """Return a new session state with updated selection."""
        return GameSessionState(self.current_state, new_selection.copy())
    
    def with_state_and_selection(self, new_state: GameState, new_selection: List[Any]) -> 'GameSessionState':
        """Return a new session state with both state and selection updated."""
        return GameSessionState(new_state, new_selection.copy())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for transmission over the WebSocket wire."""
        return {
            "current_state": self.current_state.value,
            "current_selection": [ref.name for ref in self.current_selection],
        }


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
            element_type_name = layout_element.element_type
        
        rules = GameStateManager.get_selection_rules(session.current_state)
        
        # Check if type is allowed
        if not rules.can_select_type(element_type_name):
            return False, f"Cannot select {element_type_name} in {session.current_state.value}"
        
        # Check if we can select more
        if not rules.can_select_more(len(session.current_selection)):
            return False, f"Cannot select more than {rules.max_selections} elements"
        
        # Check special rules
        if rules.special_rules:
            # Handle DISCARD_TOKENS state - only allow player tokens
            if session.current_state == GameState.DISCARD_TOKENS:
                if rules.special_rules.get("player_tokens_only"):
                    # Check if this is a player token (has "player" in metadata)
                    if "player" not in layout_element.metadata:
                        return False, "Can only select tokens from your hand"
                    # Check if it belongs to current player
                    if layout_element.metadata.get("player") != desk.current_player.name:
                        return False, "Can only select your own tokens"
            elif session.current_state == GameState.TAKE_GOLD_AND_RESERVE:
                # Special handling for TAKE_GOLD_AND_RESERVE - allow flexible ordering
                # Count what's already selected
                player = desk.current_player
                if not player.can_reserve():
                    return False, "Cannot reserve more than 3 cards"

                gold_tokens_selected = 0
                cards_selected = 0
                decks_selected = 0
                
                for selected_element in session.current_selection:
                    selected_type = selected_element.element_type
                    if selected_type == "Token" and hasattr(selected_element.element, 'color') and selected_element.element.color == "gold":
                        gold_tokens_selected += 1
                    elif selected_type == "Card" or selected_type == "Deck":
                        cards_selected += 1
                
                # Check what we're trying to select now
                if element_type_name == "Token":
                    # Only allow gold tokens
                    if not (hasattr(layout_element.element, 'color') and layout_element.element.color == "gold"):
                        return False, "Can only select gold tokens in this action"
                    # Only allow one gold token total
                    if gold_tokens_selected >= 1:
                        return False, "Can only select one gold token"
                elif element_type_name == "Card" or element_type_name == "Deck":
                    # Only allow one card total
                    if cards_selected >= 1:
                        return False, "Can only select one card or deck"
            elif session.current_state == GameState.CARD_ABILITY_2ND_COLOR:
                # Special handling for TAKE 2ND SAME ability - only allow tokens matching card color
                if element_type_name == "Token":
                    # Must be a board token (has "position" in metadata, no "player" key)
                    if "player" in layout_element.metadata:
                        return False, "Can only select tokens from the board"
                    if "position" not in layout_element.metadata:
                        return False, "Can only select tokens from the board"
                    # Token color must match the pending ability card color
                    pending_color = desk.pending_ability_card_color
                    if pending_color:
                        token_color = layout_element.element.color.upper() if hasattr(layout_element.element, 'color') else None
                        if token_color != pending_color.upper():
                            return False, f"Can only select {pending_color.lower()} tokens"
                    # Only allow one token
                    if len(session.current_selection) >= 1:
                        return False, "Can only select one token"
            elif session.current_state == GameState.CARD_ABILITY_STEAL:
                # Special handling for STEAL ability - only allow opponent's tokens (no gold)
                if element_type_name == "Token":
                    # Must be an opponent's token (has "player" in metadata, not current player)
                    if "player" not in layout_element.metadata:
                        return False, "Can only select opponent's tokens"
                    if layout_element.metadata.get("player") == desk.current_player.name:
                        return False, "Can only select opponent's tokens"
                    # Cannot steal gold tokens
                    token_color = layout_element.element.color.lower() if hasattr(layout_element.element, 'color') else None
                    if token_color == "gold":
                        return False, "Cannot steal gold tokens"
                    # Only allow one token
                    if len(session.current_selection) >= 1:
                        return False, "Can only select one token"
            elif session.current_state == GameState.CARD_ABILITY_JOKER:
                # Special handling for JOKER ability - only allow selecting bonus colors the player has
                if element_type_name == "BonusColor":
                    # Must belong to current player
                    if "player" not in layout_element.metadata:
                        return False, "Can only select your own bonuses"
                    if layout_element.metadata.get("player") != desk.current_player.name:
                        return False, "Can only select your own bonuses"
                    # Player must have at least 1 bonus of this color
                    # Get color from element (BonusColor object) or metadata
                    if hasattr(layout_element.element, 'color'):
                        color = layout_element.element.color.lower()
                    else:
                        color = layout_element.metadata.get("color", "").lower()
                    player_bonuses = desk.current_player.get_bonuses()
                    if player_bonuses.get(color, 0) <= 0:
                        return False, f"You don't have any {color} bonuses"
                    # Only allow one selection
                    if len(session.current_selection) >= 1:
                        return False, "Can only select one color"
            else:
                # Original special rules for other states
                if element_type_name == "Token":
                    if rules.special_rules.get("no_gold") and hasattr(layout_element.element, 'color') and layout_element.element.color == "gold":
                        return False, "Cannot select gold tokens in this state"
                    
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
            element_name = element_type_name or layout_element.element_type
            return new_session, True, f"Deselected {element_name}"

        # Check if we can select this element
        can_select, reason = GameStateManager.can_select_element(session, layout_element, desk, element_type_name)
        if can_select:
            new_selection = session.current_selection + [layout_element]
            new_session = session.with_selection(new_selection)
            element_name = element_type_name or layout_element.element_type
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
                
            case GameState.CHECK_DISCARD:
                return GameStateManager._handle_check_discard_buttons(session, button, desk)
                
            case GameState.DISCARD_TOKENS:
                return GameStateManager._handle_discard_tokens_buttons(session, button, desk)
                
            case GameState.ROYAL_SELECTION:
                return GameStateManager._handle_royal_selection_buttons(session, button, desk)
                
            case GameState.CONFIRM_ROUND:
                return GameStateManager._handle_confirm_round_buttons(session, button, desk)
            
            case GameState.CARD_ABILITY_2ND_COLOR:
                return GameStateManager._handle_card_ability_2nd_color_buttons(session, button, desk)
            
            case GameState.CARD_ABILITY_STEAL:
                return GameStateManager._handle_card_ability_steal_buttons(session, button, desk)
            
            case GameState.CARD_ABILITY_JOKER:
                return GameStateManager._handle_card_ability_joker_buttons(session, button, desk)
        
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
                
                # Check if it's a joker card - player must have at least 1 bonus to purchase
                if selected_card.ability and "1 COLOR" in selected_card.ability:
                    player_bonuses = desk.current_player.get_bonuses()
                    total_bonuses = sum(player_bonuses.values())
                    if total_bonuses == 0:
                        return session, None, "Cannot purchase joker card without any bonuses"
                
                # Check if purchasing from reserved (no "level" key) or from pyramid
                if "level" in selected_element.metadata:
                    # Purchasing from pyramid
                    action = Action(ActionType.PURCHASE_CARD, {
                        "card": selected_card,
                        "level": selected_element.metadata["level"],
                        "index": selected_element.metadata["index"]
                    })
                else:
                    # Purchasing from reserved cards
                    action = Action(ActionType.PURCHASE_CARD, {
                        "card": selected_card,
                        "reserved_index": selected_element.metadata["index"]
                    })
                
                # Check if card has "TAKE 2ND SAME" ability
                if selected_card.ability == "TAKE 2ND SAME":
                    # Store the card color for token selection validation
                    desk.pending_ability_card_color = selected_card.color
                    new_session = session.with_state_and_selection(GameState.CARD_ABILITY_2ND_COLOR, [])
                    return new_session, action, f"Card purchased! You may take a {selected_card.color.lower()} token from the board."
                
                # Check if card has "STEAL" ability
                if selected_card.ability == "STEAL":
                    # Store where to return after stealing
                    desk.pending_steal_return_state = "POST_ACTION_CHECKS"
                    new_session = session.with_state_and_selection(GameState.CARD_ABILITY_STEAL, [])
                    return new_session, action, "Card purchased! You may steal a token from your opponent."
                
                # Check if card has joker ability ("1 COLOR" or "1 COLOR/TURN")
                if selected_card.ability and "1 COLOR" in selected_card.ability:
                    # Store the card for color assignment
                    desk.pending_joker_card = selected_card
                    # Check if it also grants extra turn
                    if "TURN" in selected_card.ability:
                        desk.set_extra_turn()
                    new_session = session.with_state_and_selection(GameState.CARD_ABILITY_JOKER, [])
                    return new_session, action, "Card purchased! Choose a color for your joker card."
                
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
                can_confirm, reason = GameStateManager.can_confirm_selection(session, desk)
                if not can_confirm:
                    return session, None, reason
                
                # Validate that we have exactly one gold token and one card
                gold_token_layout_element = None
                card_layout_element = None
                
                for selected_element in session.current_selection:
                    element_type = selected_element.element_type
                    if element_type == "Token" and hasattr(selected_element.element, 'color') and selected_element.element.color == "gold":
                        gold_token_layout_element = selected_element
                    elif element_type == "Card" or element_type == "Deck":
                        card_layout_element = selected_element
                
                if gold_token_layout_element is None:
                    return session, None, "Must select exactly one gold token"
                if card_layout_element is None:
                    return session, None, "Must select exactly one card"
                
                # Determine if reserving from face-down deck or visible pyramid card
                is_deck_reservation = card_layout_element.element_type == "Deck"
                
                if is_deck_reservation:
                    card = card_layout_element.element.draw(1)[0]
                else:
                    card = card_layout_element.element
                
                action = Action(ActionType.TAKE_GOLD_AND_RESERVE, {
                    "gold_token": gold_token_layout_element.element,
                    "gold_token_positions": gold_token_layout_element.metadata.get("position"),
                    "card": card,
                    "card_level": card_layout_element.metadata.get("level"),
                    "card_index": card_layout_element.metadata.get("index"),
                    "is_deck_reservation": is_deck_reservation
                })


                
                new_session = session.with_state_and_selection(GameState.POST_ACTION_CHECKS, [])
                return new_session, action, "Gold taken and card reserved successfully"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_post_action_checks_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in POST_ACTION_CHECKS state."""
        match button.action:
            case "continue_to_confirm_round":
                player = desk.current_player
                
                # Check if player qualifies for a royal card (before discard check)
                # Check if any royals are still available (not None)
                available_royals = any(royal is not None for royal in desk.royals.values())
                if player.qualifies_for_royal() and available_royals:
                    new_session = session.with_state(GameState.ROYAL_SELECTION)
                    crown_milestone = 3 if 3 not in player.royals_claimed_at else 6
                    return new_session, None, f"You reached {crown_milestone} crowns! Select a royal card."
                
                # Otherwise, proceed to check discard
                new_session = session.with_state(GameState.CHECK_DISCARD)
                return new_session, None, "Checking token count..."
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_check_discard_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in CHECK_DISCARD state - automatically routes to discard or confirm."""
        match button.action:
            case "continue":
                player = desk.current_player
                
                # Check if player needs to discard tokens
                if player.get_token_count() > 10:
                    new_session = session.with_state(GameState.DISCARD_TOKENS)
                    return new_session, None, f"You have {player.get_token_count()} tokens. Discard down to 10."
                else:
                    new_session = session.with_state(GameState.CONFIRM_ROUND)
                    return new_session, None, "Ready to confirm round"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_discard_tokens_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in DISCARD_TOKENS state."""
        match button.action:
            case "confirm_discard":
                player = desk.current_player
                tokens_to_discard = session.current_selection
                
                # Validate selection
                current_count = player.get_token_count()
                discard_count = len(tokens_to_discard)
                remaining = current_count - discard_count
                
                # Must select at least 1 token
                if discard_count == 0:
                    return session, None, "Must select at least 1 token to discard"
                
                # Cannot discard more than needed (would leave player with <10 tokens)
                if remaining < 10:
                    return session, None, f"Cannot discard {discard_count} tokens - would leave you with only {remaining}"

                # Create action to discard tokens
                action = Action(ActionType.DISCARD_TOKENS, {
                    "tokens": [elem.element for elem in tokens_to_discard]
                })
                
                # After discarding, route to CHECK_DISCARD to see if more discarding is needed
                new_session = session.with_state_and_selection(GameState.CHECK_DISCARD, [])
                return new_session, action, f"Discarded {discard_count} token(s). Checking token count..."

        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_royal_selection_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in ROYAL_SELECTION state."""
        match button.action:
            case "confirm_royal":
                can_confirm, reason = GameStateManager.can_confirm_selection(session, desk)
                if not can_confirm:
                    return session, None, reason
                
                # Get the selected royal
                selected_element = session.current_selection[0]
                selected_royal = selected_element.element
                royal_index = selected_element.metadata.get("index")
                
                # Create the action
                action = Action(ActionType.CLAIM_ROYAL, {
                    "royal": selected_royal,
                    "index": royal_index
                })
                
                # Check if royal has "STEAL" ability
                if hasattr(selected_royal, 'ability') and selected_royal.ability == "STEAL":
                    # Store where to return after stealing (from royal, return to CHECK_DISCARD)
                    desk.pending_steal_return_state = "CHECK_DISCARD"
                    new_session = session.with_state_and_selection(GameState.CARD_ABILITY_STEAL, [])
                    return new_session, action, "Royal claimed! You may steal a token from your opponent."
                
                # After claiming royal, route to CHECK_DISCARD
                new_session = session.with_state_and_selection(GameState.CHECK_DISCARD, [])
                return new_session, action, "Royal claimed! Checking token count..."
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_confirm_round_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in CONFIRM_ROUND state."""
        match button.action:
            case "finish_round":
                # Fill empty pyramid slots now that the round is confirmed
                # This prevents player from seeing next card and rolling back
                filled_count = desk.pyramid.fill_all_empty_slots()
                
                # Check for victory BEFORE moving to next player or extra turn
                victory_info = desk.current_player.get_victory_info()
                if victory_info:
                    # Player has won! Set winner and transition to GAME_OVER
                    desk.winner = desk.current_player_index
                    new_session = session.with_state_and_selection(GameState.GAME_OVER, [])
                    return new_session, None, f"🎉 {desk.current_player.name} wins by reaching {victory_info['value']} {victory_info['condition']}!"
                
                # Check if player has an extra turn from TURN ability
                if desk.has_extra_turn():
                    desk.clear_extra_turn()
                    new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                    return new_session, None, f"Extra turn! {desk.current_player.name} goes again!"
                else:
                    desk.next_player()
                    new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                    return new_session, None, "Round finished - next player's turn"
            case "rollback_to_start":
                # The controller will handle the actual rollback
                # Clear extra turn flag on rollback
                desk.clear_extra_turn()
                new_session = session.with_state_and_selection(GameState.START_OF_ROUND, [])
                return new_session, None, "Rolled back to start of round"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_card_ability_2nd_color_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in CARD_ABILITY_2ND_COLOR state (TAKE 2ND SAME ability)."""
        match button.action:
            case "confirm_selection":
                # Check if player selected a token
                if len(session.current_selection) == 1:
                    # Take the selected token
                    selected_element = session.current_selection[0]
                    action = Action(ActionType.TAKE_ABILITY_TOKEN, {
                        "token": selected_element.element,
                        "position": selected_element.metadata["position"]
                    })
                    new_session = session.with_state_and_selection(GameState.POST_ACTION_CHECKS, [])
                    return new_session, action, f"Took a {selected_element.element.color} token!"
                else:
                    # No token selected, just proceed
                    # Clear the pending ability card color
                    desk.pending_ability_card_color = None
                    new_session = session.with_state_and_selection(GameState.POST_ACTION_CHECKS, [])
                    return new_session, None, "Skipped taking a token"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_card_ability_steal_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in CARD_ABILITY_STEAL state (STEAL ability from card or royal)."""
        match button.action:
            case "confirm_selection":
                # Determine which state to return to based on where steal was triggered
                return_state = desk.pending_steal_return_state
                if return_state == "CHECK_DISCARD":
                    next_state = GameState.CHECK_DISCARD
                else:
                    next_state = GameState.POST_ACTION_CHECKS
                
                # Check if player selected a token
                if len(session.current_selection) == 1:
                    # Steal the selected token
                    selected_element = session.current_selection[0]
                    action = Action(ActionType.STEAL_TOKEN, {
                        "token": selected_element.element
                    })
                    new_session = session.with_state_and_selection(next_state, [])
                    return new_session, action, f"Stole a {selected_element.element.color} token from opponent!"
                else:
                    # No token selected, just proceed
                    # Clear the pending steal return state
                    desk.pending_steal_return_state = None
                    new_session = session.with_state_and_selection(next_state, [])
                    return new_session, None, "Skipped stealing a token"
        return session, None, f"Unknown action: {button.action}"
    
    @staticmethod
    def _handle_card_ability_joker_buttons(session: GameSessionState, button: ActionButton, desk: Any) -> Tuple[GameSessionState, Optional[Action], str]:
        """Handle buttons in CARD_ABILITY_JOKER state (1 COLOR ability)."""
        match button.action:
            case "confirm_selection":
                # Player must select a color (mandatory)
                if len(session.current_selection) != 1:
                    return session, None, "Must select a color for your joker card"
                
                # Get the selected color from BonusColor element or metadata
                selected_element = session.current_selection[0]
                if hasattr(selected_element.element, 'color'):
                    selected_color = selected_element.element.color
                else:
                    selected_color = selected_element.metadata.get("color", "")
                
                # Create action to assign the color to the joker card
                action = Action(ActionType.ASSIGN_JOKER_COLOR, {
                    "color": selected_color
                })
                
                new_session = session.with_state_and_selection(GameState.POST_ACTION_CHECKS, [])
                return new_session, action, f"Joker card is now {selected_color.upper()}!"
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
                
            case GameState.CHECK_DISCARD:
                explanation = "Checking token count..."
                buttons = [
                    ActionButton("Continue", "continue")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.DISCARD_TOKENS:
                player = desk.current_player
                current_count = player.get_token_count()
                need_to_discard = current_count - 10
                selected_count = len(session.current_selection)
                explanation = f"You have {current_count} tokens. Discard at least 1 (selected: {selected_count})"
                buttons = [
                    ActionButton("Confirm Discard", "confirm_discard", enabled=(selected_count > 0))
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.ROYAL_SELECTION:
                player = desk.current_player
                crown_milestone = 3 if 3 not in player.royals_claimed_at else 6
                selected_count = len(session.current_selection)
                explanation = f"Congratulations! You reached {crown_milestone} crowns. Select a royal card."
                buttons = [
                    ActionButton("Confirm Royal", "confirm_royal", enabled=(selected_count == 1))
                ]
                return CurrentAction(session.current_state, explanation, buttons)
                
            case GameState.CONFIRM_ROUND:
                # Check if player has extra turn
                extra_turn_msg = " (Extra Turn!)" if desk.has_extra_turn() else ""
                explanation = f"Finish this round?{extra_turn_msg}"
                buttons = [
                    ActionButton("Yes", "finish_round"),
                    ActionButton("No", "rollback_to_start")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
            
            case GameState.CARD_ABILITY_2ND_COLOR:
                # TAKE 2ND SAME ability - player can take a token matching the card color
                card_color = desk.pending_ability_card_color or "matching"
                selected_count = len(session.current_selection)
                if selected_count == 0:
                    explanation = f"You may take a {card_color.lower()} token from the board (optional)"
                else:
                    explanation = f"Selected 1 {card_color.lower()} token"
                buttons = [
                    ActionButton("Confirm selection", "confirm_selection")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
            
            case GameState.CARD_ABILITY_STEAL:
                # STEAL ability - player can steal a token from opponent
                selected_count = len(session.current_selection)
                if selected_count == 0:
                    explanation = "You may steal a gem or pearl token from your opponent (optional)"
                else:
                    selected_token = session.current_selection[0].element
                    explanation = f"Selected 1 {selected_token.color} token to steal"
                buttons = [
                    ActionButton("Confirm selection", "confirm_selection")
                ]
                return CurrentAction(session.current_state, explanation, buttons)
            
            case GameState.CARD_ABILITY_JOKER:
                # JOKER ability - player must choose a color for the joker card
                selected_count = len(session.current_selection)
                if selected_count == 0:
                    explanation = "Select a bonus color to assign to your joker card"
                else:
                    # Get color from BonusColor element or metadata
                    selected_element = session.current_selection[0]
                    if hasattr(selected_element.element, 'color'):
                        selected_color = selected_element.element.color
                    else:
                        selected_color = selected_element.metadata.get("color", "")
                    explanation = f"Joker card will become {selected_color.upper()}"
                buttons = [
                    ActionButton("Confirm selection", "confirm_selection", enabled=(selected_count == 1))
                ]
                return CurrentAction(session.current_state, explanation, buttons)
            
            case GameState.GAME_OVER:
                # Game has ended - show victory message with no buttons
                winner = desk.players[desk.winner] if desk.winner is not None else None
                if winner:
                    victory_info = winner.get_victory_info()
                    if victory_info:
                        explanation = f"🎉 GAME OVER - {winner.name} wins by reaching {victory_info['value']} {victory_info['condition']}! 🎉"
                    else:
                        explanation = f"🎉 GAME OVER - {winner.name} wins! 🎉"
                else:
                    explanation = "🎉 GAME OVER 🎉"
                # No buttons - game is frozen
                return CurrentAction(session.current_state, explanation, [])
                
        return CurrentAction(session.current_state, "Unknown state", []) 