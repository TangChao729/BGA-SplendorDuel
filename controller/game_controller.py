import pygame
import sys
import os
import copy
from typing import Tuple, Optional, List

# Import from the correct locations based on your directory structure
from model.desk import Desk           # desk.py is in model/ directory
from model.player import PlayerState
from model.tokens import Token
from model.cards import Card
from model.actions import ActionType, Action, ActionButton  # Basic action classes
from model.game_state_machine import GameState, CurrentAction, GameSessionState, GameStateManager  # State machine classes
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
        self.current_state: GameState = GameState.START_OF_ROUND
        self.current_player_index: int = 0
        
        # Initialize session state for stateless GSM
        self.session_state = GameSessionState(
            current_state=GameState.START_OF_ROUND,
            current_selection=[]
        )
        

    def run(self):
        """Main Pygame loop: handle events, update model, render view."""
        self.desk_snapshot: Desk = copy.deepcopy(self.desk)
        while self.running:
            # record the start state when change player
            if self.desk.current_player_index != self.current_player_index:
                self.desk_snapshot = copy.deepcopy(self.desk)
                self.current_player_index = self.desk.current_player_index
            # Use stateless function to get current action
            self.current_action: CurrentAction = GameStateManager.get_current_action(self.session_state, self.desk)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    action = self._interpret_click(event.pos)
                    if action:
                        self.desk.apply_action(action)
                        self.dialogue = f"Action executed: {action.type.name}"
            
            # Use session state for rendering
            self.view.render(self.desk, self.dialogue, self.current_action, self.session_state.current_selection)
            self.clock.tick(30)
        pygame.quit()

    def _interpret_click(self, pos: Tuple[int, int]) -> Optional[Action]:
        """
        Map a screen click (x,y) to a game Action, or None if click is irrelevant.
        Uses the layout registry to detect clicks on game elements.
        """
        layout_element = self.view.layout_registry.find_element_at(pos)
        if not layout_element:
            self.dialogue = f"Click at {pos} - no element found"
            return None
        
        self.dialogue = f"Clicked {layout_element.element_type.__name__}: {layout_element.name}"

        if layout_element.element_type != ActionButton:
            self._handle_element_selection(layout_element)
        else:
            button: ActionButton = layout_element.element
            return self._handle_action_button_click(button)
        
        return None
    
    def _handle_element_selection(self, layout_element: LayoutElement) -> None:
        """Handle element selection using stateless GameStateManager."""
        element_type_name = type(layout_element.element).__name__
        
        # Use stateless function
        new_session, success, message = GameStateManager.select_element(
            self.session_state, layout_element, self.desk, element_type_name
        )
        
        # Update session state
        self.session_state = new_session
        self.dialogue = message

    def _handle_action_button_click(self, button: ActionButton) -> Optional[Action]:
        """Handle clicks on action panel buttons using stateless GameStateManager."""
        
        # Use stateless function
        new_session, action, message = GameStateManager.handle_button_click(
            self.session_state, button, self.desk
        )
        
        # Update session state and controller state
        self.session_state = new_session
        self.current_state = new_session.current_state
        
        # Handle special cases that require controller-level operations
        if button.action == "rollback_to_start" and hasattr(self, 'desk_snapshot'):
            self.desk = copy.deepcopy(self.desk_snapshot)
            # Reset session state to clear selections
            self.session_state = self.session_state.with_selection([])
            message = "Rolled back to start of round"
        
        # Update dialogue with the message from state machine
        self.dialogue = message
        
        return action

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
    ctrl.desk.board.grid[0][0] = None
    ctrl.desk.board.grid[0][1] = None
    ctrl.desk.board.grid[1][1] = None
    player1.tokens = {Token('red'): 3}
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