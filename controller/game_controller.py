import pygame
import sys
import os
from typing import Tuple, Optional, List

# Import from the correct locations based on your directory structure
from model.desk import Desk           # desk.py is in model/ directory
from model.player import PlayerState
from model.tokens import Token
from model.actions import ActionType, Action, GameState, CurrentAction, ActionButton  # actions.py is in model/ directory
from view.assets import AssetManager  # assets.py is in view/ directory
from view.game_view import GameView   # game_view.py is in view/ directory
from view.layout import LayoutElement

# Screen dimensions (should match those in game_view)
from view.game_view import SCREEN_WIDTH, SCREEN_HEIGHT

class GameController:
    """
    Orchestrates the Pygame loop, translating user input into model Actions
    and using GameView to render the Desk state.
    """
    def __init__(self, card_json: str, token_json: str, royal_json: str, initial_privileges: int = 3, asset_path: str = "data/images"):
        # Initialize Pygame and create window
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Splendor Duel")
        # Load assets and view
        self.assets = AssetManager(asset_path)
        self.view = GameView(self.screen, self.assets)
        # Initialize game model
        self.desk = Desk(card_json, token_json, royal_json, initial_privileges)
        self.dialogue = "Welcome to Splendor Duel!"
        self.clock = pygame.time.Clock()
        self.running = True
        # Click state management
        self.selected_tokens: List[Tuple[int, int]] = []  # (row, col) coordinates
        self.selected_cards: List[Tuple[int, int]] = []   # (level, index) coordinates
        self.current_state: GameState = GameState.START_OF_ROUND
        self.pending_action_button: Optional[ActionButton] = None
        self.info_message: str = ""
        self.pending_action: Optional[Action] = None
        self.current_selection: Optional[LayoutElement] = []
        self.current_player_index: int = 0
        self.desk_snapshot: Desk = None

    def run(self):
        """Main Pygame loop: handle events, update model, render view."""
        # print(self.desk.board.eligible_draws())
        while self.running:
            # record the start state when change player
            if self.desk.current_player_index != self.current_player_index:
                self.desk_snapshot = self.desk.deepcopy()
                self.current_player_index = self.desk.current_player_index
            self.current_action: CurrentAction = self.desk.get_current_action(state=self.current_state)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    action = self._interpret_click(event.pos)
                    if action:
                        try:
                            self.desk.apply_action(action)
                            # self.selected_tokens.clear()
                            # self.selected_cards.clear()
                            self.dialogue = f"Action executed: {action.type.name}"
                            # After a mandatory action, go to post_action_checks state
                            # self.current_state = GameState.POST_ACTION_CHECKS
                            # self.current_action = self.desk.get_current_action(state=self.current_state)
                            # self.pending_action_button = None
                            # self.info_message = ""
                            # self.pending_action = None
                        except Exception as e:
                            self.dialogue = str(e)
            # Pass current_action to GameView
            self.view.render(self.desk, self.dialogue, self.current_action, self.current_selection)
            self.clock.tick(30)
        pygame.quit()

    def _interpret_click(self, pos: Tuple[int, int]) -> Optional[Action]:
        """
        Map a screen click (x,y) to a game Action, or None if click is irrelevant.
        Uses the layout registry to detect clicks on game elements.
        """
        element = self.view.layout_registry.find_element_at(pos)
        if not element:
            self.dialogue = f"Click at {pos} - no element found"
            return None
        
        self.dialogue = f"Clicked {element.element_type.__name__}: {element.name}"

        if element.element_type != ActionButton:
            self._handle_element_selection(element)
        else:
            button: ActionButton = element.element
            return self._handle_action_button_click(button)
        
        return None
    
    def _handle_element_selection(self, element: LayoutElement) -> None:
        """Handle element selection."""
        match self.current_state:

            # During start of round, no elements can be selected
            case GameState.START_OF_ROUND:
                allowed_selections = []
                if element.element_type in allowed_selections:
                    if element not in self.current_selection:
                        self.current_selection.append(element)
                    else:
                        self.current_selection.remove(element)
                else:
                    self.dialogue = f"Cannot select {element.name} in {self.current_state.name}"
                    return None
                
            # During privilege use, only token and only one token can be selected
            case GameState.USE_PRIVILEGE:
                allowed_selections = [Token]
                if element.element_type in allowed_selections:
                    if element not in self.current_selection:
                        if len(self.current_selection) < 1:
                            self.current_selection.append(element)
                        else:
                            self.dialogue = "Cannot select more than 1 token"
                            return None
                    else:
                        self.current_selection.remove(element)
                else:
                    self.dialogue = f"Cannot select {element.name} in {self.current_state.name}"
                    return None
                
            # During take tokens, only tokens can be selected
            case GameState.TAKE_TOKENS:
                allowed_selections = [Token]
                if element.element_type in allowed_selections:
                    if element not in self.current_selection:
                        if len(self.current_selection) < 3:
                            self.current_selection.append(element)
                        else:
                            self.dialogue = "Cannot select more than 3 tokens"
                            return None
                    else:
                        self.current_selection.remove(element)
                else:
                    self.dialogue = f"Cannot select {element.name} in {self.current_state.name}"
                    return None

    def _handle_action_button_click(self, button: ActionButton) -> Optional[Action]:
        """Handle clicks on action panel buttons and manage state transitions."""
        
        match self.current_state:
            case GameState.START_OF_ROUND:
                # Handle action selection
                match button.action:
                    case "use_privilege":
                        self.current_state = GameState.USE_PRIVILEGE
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                    case "replenish_board":
                        self.current_state = GameState.REPLENISH_BOARD
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                    case "purchase_card":
                        self.current_state = GameState.PURCHASE_CARD
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                    case "take_tokens":
                        self.current_state = GameState.TAKE_TOKENS
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                    case "take_gold_and_reserve":
                        self.current_state = GameState.TAKE_GOLD_AND_RESERVE
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                        
            case GameState.USE_PRIVILEGE:
                match button.action:
                    case "cancel":
                        self.current_state = GameState.START_OF_ROUND
                        self.current_selection.clear()
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                    case "confirm":
                        if len(self.current_selection) != 1:
                            self.dialogue = "Must select exactly 1 token"
                            return None
                        self.current_state = GameState.START_OF_ROUND
                        action = Action(ActionType.USE_PRIVILEGE, {"token": self.current_selection[0].element, "position": self.current_selection[0].metadata["position"]})
                        self.current_selection.clear()
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return action
                
            case GameState.REPLENISH_BOARD:
                if button.action == "confirm_replenish":
                    # TODO: Implement replenish board action
                    action = Action(ActionType.REPLENISH_BOARD, {})
                    self.current_state = GameState.CHOOSE_MANDATORY_ACTION
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return action
                elif button.action == "cancel":
                    self.current_state = GameState.START_OF_ROUND
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return None
                    
            case GameState.CHOOSE_MANDATORY_ACTION:
                match button.action:
                    case "purchase_card":
                        self.current_state = GameState.PURCHASE_CARD
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                    case "take_tokens":
                        self.current_state = GameState.TAKE_TOKENS
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                    case "take_gold_and_reserve":
                        self.current_state = GameState.TAKE_GOLD_AND_RESERVE
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return None
                        
            case GameState.PURCHASE_CARD:
                if button.action == "cancel":
                    self.current_state = GameState.START_OF_ROUND
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return None
                # TODO: Handle card selection for purchase
                
            case GameState.TAKE_TOKENS:
                if button.action == "cancel":
                    self.current_state = GameState.START_OF_ROUND
                    self.current_selection.clear()
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return None
                elif button.action == "confirm":
                    if len(self.current_selection) > 3:
                        self.dialogue = "Cannot select more than 3 tokens"
                        return None
                    elif len(self.current_selection) < 1:
                        self.dialogue = "Must select at least 1 token"
                        return None
                    else:
                        eligible_draws = self.desk.board.eligible_draws()
                        combo = {}
                        for element in self.current_selection:
                            combo[element.element] = combo.get(element.element, []) + [element.metadata["position"]]
                        if combo not in eligible_draws:
                            self.dialogue = "Selected tokens are not eligible for taking"
                            return None
                        self.current_state = GameState.START_OF_ROUND
                        action = Action(ActionType.TAKE_TOKENS, {"combo": combo})
                        self.current_selection.clear()
                        self.current_action = self.desk.get_current_action(state=self.current_state)
                        return action
                
            case GameState.TAKE_GOLD_AND_RESERVE:
                if button.action == "cancel":
                    self.current_state = GameState.START_OF_ROUND
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return None
                # TODO: Handle gold token and card selection
                
            case GameState.POST_ACTION_CHECKS:
                if button.action == "continue_to_confirm_round":
                    self.current_state = GameState.CONFIRM_ROUND
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return None
                    
            case GameState.CONFIRM_ROUND:
                if button.action == "finish_round":
                    # End the round, switch player, reset state
                    self.current_state = GameState.START_OF_ROUND
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return None
                elif button.action == "rollback_to_start":
                    # Roll back to start_of_round
                    self.current_state = GameState.START_OF_ROUND
                    # restore the desk to the start of round
                    self.desk = self.desk_snapshot.deepcopy()
                    self.current_action = self.desk.get_current_action(state=self.current_state)
                    return None
        
        # Fallback: do nothing
        return None

    def _handle_token_click(self, element) -> Optional[Action]:
        """Handle clicks on tokens in the board grid."""
        row = element.metadata["row"]
        col = element.metadata["col"]
        color = element.metadata["color"]
        
        # Check if this token is already selected
        if (row, col) in self.selected_tokens:
            # Deselect the token
            self.selected_tokens.remove((row, col))
            self.dialogue = f"Deselected {color} token at ({row}, {col})"
            return None
        
        # Check if we can add this token to selection
        if len(self.selected_tokens) >= 3:
            self.dialogue = "Cannot select more than 3 tokens"
            return None
        
        # Check if this token forms a valid line with already selected tokens
        if self.selected_tokens and not self._is_valid_token_line(row, col):
            self.dialogue = "Tokens must be in a straight line"
            return None
        
        # Add token to selection
        self.selected_tokens.append((row, col))
        self.dialogue = f"Selected {color} token at ({row}, {col}) - {len(self.selected_tokens)}/3"
        
        # If we have a valid combination, create action
        if len(self.selected_tokens) >= 1:
            return self._create_take_tokens_action()
        
        return None

    def _handle_pyramid_card_click(self, element) -> Optional[Action]:
        """Handle clicks on pyramid cards."""
        level = element.metadata["level"]
        index = element.metadata["index"]
        card = element.metadata["card"]
        
        # Check if player can afford the card
        if self.desk.current_player.can_afford(card):
            self.dialogue = f"Purchasing card: {card.id} (Level {level}, Index {index})"
            return Action(ActionType.PURCHASE_CARD, {"level": level, "index": index})
        else:
            self.dialogue = f"Cannot afford card: {card.id}"
            return None

    def _handle_reserved_card_click(self, element) -> Optional[Action]:
        """Handle clicks on reserved cards."""
        index = element.metadata["index"]
        card = element.metadata["card"]
        
        # Check if player can afford the card
        if self.desk.current_player.can_afford(card):
            self.dialogue = f"Purchasing reserved card: {card.id}"
            return Action(ActionType.PURCHASE_CARD, {"reserved_index": index})
        else:
            self.dialogue = f"Cannot afford reserved card: {card.id}"
            return None

    def _handle_privilege_click(self, element) -> Optional[Action]:
        """Handle clicks on privilege scrolls."""
        if self.desk.current_player.privileges > 0:
            self.dialogue = "Using privilege - select a token to take"
            # For now, just take a black token (simplified)
            # In a full implementation, you'd want a token selection UI
            return Action(ActionType.USE_PRIVILEGE, {"token": "black"})
        else:
            self.dialogue = "No privileges available"
            return None

    def _handle_royal_click(self, element) -> Optional[Action]:
        """Handle clicks on royal cards."""
        # Royal cards are typically not directly clickable for actions
        # They're usually awarded automatically when conditions are met
        self.dialogue = "Royal cards are awarded automatically"
        return None

    def _is_valid_token_line(self, new_row: int, new_col: int) -> bool:
        """Check if a new token position forms a valid line with selected tokens."""
        if not self.selected_tokens:
            return True
        
        # Get all positions including the new one
        positions = self.selected_tokens + [(new_row, new_col)]
        
        # Check if all positions are in a straight line
        if len(positions) == 1:
            return True
        
        # Check horizontal line
        if all(pos[0] == positions[0][0] for pos in positions):
            cols = sorted(pos[1] for pos in positions)
            return cols == list(range(cols[0], cols[0] + len(cols)))
        
        # Check vertical line
        if all(pos[1] == positions[0][1] for pos in positions):
            rows = sorted(pos[0] for pos in positions)
            return rows == list(range(rows[0], rows[0] + len(rows)))
        
        # Check diagonal lines (both directions)
        # Diagonal 1: row + col is constant
        if all(pos[0] + pos[1] == positions[0][0] + positions[0][1] for pos in positions):
            return True
        
        # Diagonal 2: row - col is constant
        if all(pos[0] - pos[1] == positions[0][0] - positions[0][1] for pos in positions):
            return True
        
        return False

    def _create_take_tokens_action(self) -> Optional[Action]:
        """Create a TAKE_TOKENS action from selected tokens."""
        if not self.selected_tokens:
            return None
        
        # Group tokens by color
        token_groups = {}
        for row, col in self.selected_tokens:
            token = self.desk.board.grid[row][col]
            if token:
                color = token.color
                if color not in token_groups:
                    token_groups[color] = []
                token_groups[color].append((row, col))
        
        # Create the combo dictionary
        combo = {color: positions for color, positions in token_groups.items()}
        
        self.dialogue = f"Taking tokens: {combo}"
        return Action(ActionType.TAKE_TOKENS, {"combo": combo})

# Entry-point example
if __name__ == '__main__':
    # Load paths from data/box.yaml or hard-code
    import yaml
    with open('data/box.yaml','r') as f:
        cfg = yaml.safe_load(f)
    ctrl = GameController(
        card_json=cfg['cards'],
        token_json=cfg['tokens'],
        royal_json=cfg['royals'],
        initial_privileges=cfg.get('privileges',3),
        asset_path='data/images'
    )
    player1 = PlayerState("Player 1")
    player1.privileges = 3
    player2 = PlayerState("Player 2")
    ctrl.desk.add_player(player1, player2)

    # add artificial player data for testing
    ctrl.desk.board.fill_grid(ctrl.desk.bag.draw())
        # ctrl.desk.players[0].privileges = 3
    # ctrl.desk.players[0].tokens['black'] = 2
    # ctrl.desk.players[0].tokens['red'] = 1
    # ctrl.desk.players[0].tokens['green'] = 1
    # ctrl.desk.players[0].tokens['blue'] = 1
    # ctrl.desk.players[0].tokens['white'] = 1
    # ctrl.desk.players[0].tokens['pearl'] = 1
    # ctrl.desk.players[0].tokens['gold'] = 1
    
    # ctrl.desk.players[0].bonuses['black'] = 1
    # ctrl.desk.players[0].bonuses['red'] = 1
    # ctrl.desk.players[0].bonuses['green'] = 1
    # ctrl.desk.players[0].bonuses['blue'] = 1
    # ctrl.desk.players[0].bonuses['white'] = 1   
    
    # ctrl.desk.players[0].reserved.append(ctrl.desk.pyramid.decks.get(1).draw())  # reserve a card for testing
    # ctrl.desk.board.grid[0][0] = Token('black')
    # ctrl.desk.board.grid[1][1] = Token('red')
    # ctrl.desk.board.grid[2][2] = Token('green')
    # ctrl.desk.board.grid[3][3] = Token('blue')
    # ctrl.desk.board.grid[4][4] = Token('white')
    ctrl.run()