import pygame
import sys
import os
from typing import Tuple, Optional

# Import from the correct locations based on your directory structure
from model.desk import Desk           # desk.py is in model/ directory
from model.tokens import Token
from model.actions import ActionType, Action  # actions.py is in model/ directory
from view.assets import AssetManager  # assets.py is in view/ directory
from view.game_view import GameView   # game_view.py is in view/ directory

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

    def run(self):
        """Main Pygame loop: handle events, update model, render view."""
        while self.running:
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
                        except Exception as e:
                            # invalid action or game over
                            self.dialogue = str(e)
            # Render current state
            self.view.render(self.desk, self.dialogue)
            self.clock.tick(30)
        pygame.quit()

    def _interpret_click(self, pos: Tuple[int, int]) -> Optional[Action]:
        """
        Map a screen click (x,y) to a game Action, or None if click is irrelevant.
        TODO: implement token-cell detection, pyramid detection, sidebar buttons.
        """
        x, y = pos
        # Example stub: always return TAKE_TOKENS of first legal combo
        # legal = self.desk.legal_actions()
        # for act in legal:
        #     if act.type == ActionType.TAKE_TOKENS:
        #         return act
        self.dialogue = "Click detected at {}, {}".format(x, y)
        return None

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

    # add artificial player data for testing
    ctrl.desk.players[0].privileges = 3
    ctrl.desk.players[0].tokens['black'] = 2
    ctrl.desk.players[0].tokens['red'] = 1
    ctrl.desk.players[0].tokens['green'] = 1
    ctrl.desk.players[0].tokens['blue'] = 1
    ctrl.desk.players[0].tokens['white'] = 1
    ctrl.desk.players[0].tokens['pearl'] = 1
    ctrl.desk.players[0].tokens['gold'] = 1
    
    ctrl.desk.players[0].bonuses['black'] = 1
    ctrl.desk.players[0].bonuses['red'] = 1
    ctrl.desk.players[0].bonuses['green'] = 1
    ctrl.desk.players[0].bonuses['blue'] = 1
    ctrl.desk.players[0].bonuses['white'] = 1   
    
    ctrl.desk.players[0].reserved.append(ctrl.desk.pyramid.decks.get(1).draw())  # reserve a card for testing
    ctrl.desk.board.grid[0][0] = Token('black')
    ctrl.desk.board.grid[1][1] = Token('red')
    ctrl.desk.board.grid[2][2] = Token('green')
    ctrl.desk.board.grid[3][3] = Token('blue')
    ctrl.desk.board.grid[4][4] = Token('white')
    ctrl.run()