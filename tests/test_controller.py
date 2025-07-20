import pytest
import pygame
import yaml
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Tuple, Optional

from controller.game_controller import GameController
from model.actions import GameState, ActionType, Action
from model.cards import Card
from model.player import PlayerState
from model.tokens import Token
from view.layout import LayoutElement, ActionButton


class TestGameControllerAutomated:
    """Automated tests for GameController with real environment but hidden screen."""
    
    @pytest.fixture
    def headless_controller(self):
        """Create a GameController with real pygame but hidden display."""
        # Set environment variable to hide pygame window
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        # Load config
        with open('data/box.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        
        # Create controller with real pygame (but hidden)
        ctrl = GameController(
            card_json=cfg['cards'],
            token_json=cfg['tokens'],
            royal_json=cfg['royals'],
            initial_privileges=cfg.get('privileges', 3),
            asset_path='data/images'
        )
        
        # Set up test players
        player1 = PlayerState("Player 1")
        player1.privileges = 3
        player2 = PlayerState("Player 2")
        ctrl.desk.add_player(player1, player2)
        
        # Set up test board state
        ctrl.desk.board.fill_grid(ctrl.desk.bag.draw())
        ctrl.desk.board.grid[0][0] = None
        ctrl.desk.board.grid[0][1] = None
        ctrl.desk.board.grid[1][1] = None
        player1.tokens = {Token('red'): 3}
        
        # Render the view to populate the layout registry
        ctrl.current_action = ctrl.desk.get_current_action(state=ctrl.current_state)
        ctrl.view.render(ctrl.desk, ctrl.dialogue, ctrl.current_action, ctrl.current_selection)
        
        yield ctrl
        
        # Cleanup
        pygame.quit()
    
    def test_controller_initialization(self, headless_controller):
        """Test that controller initializes correctly."""
        assert headless_controller.desk is not None
        assert headless_controller.current_state == GameState.START_OF_ROUND
        assert len(headless_controller.desk.players) == 2
        assert headless_controller.running is True

    def test_registry(self, headless_controller):
        """Test that the registry is populated correctly."""
        assert headless_controller.view.layout_registry is not None
        assert len(headless_controller.view.layout_registry.elements) > 0

    def test_start_of_round_buttons(self, headless_controller):
        """Test that start of round buttons are correct."""
        assert headless_controller.current_state == GameState.START_OF_ROUND
        current_button_elements = headless_controller.view.layout_registry.find_elements_by_type(ActionButton)
        assert len(current_button_elements) == 3
        assert any(layout_element.element.action == "use_privilege" for layout_element in current_button_elements)
        assert any(layout_element.element.action == "purchase_card" for layout_element in current_button_elements)
        assert any(layout_element.element.action == "take_tokens" for layout_element in current_button_elements)
    
    def test_use_privilege_button(self, headless_controller):
        """Test that use privilege button is correct."""
        assert headless_controller.current_state == GameState.START_OF_ROUND
        current_button_elements = headless_controller.view.layout_registry.find_elements_by_type(ActionButton)
        use_privilege_button = next(layout_element for layout_element in current_button_elements if layout_element.element.action == "use_privilege")
        assert use_privilege_button is not None
        assert use_privilege_button.element.action == "use_privilege"
        # mimic a click on the use privilege button
        headless_controller.current_state = GameState.USE_PRIVILEGE
        headless_controller.current_action = headless_controller.desk.get_current_action(state=headless_controller.current_state)
        headless_controller.view.render(headless_controller.desk, headless_controller.dialogue, headless_controller.current_action, headless_controller.current_selection)
        assert headless_controller.current_state == GameState.USE_PRIVILEGE
        current_button_elements = headless_controller.view.layout_registry.find_elements_by_type(ActionButton)
        assert len(current_button_elements) == 2
        assert any(layout_element.element.action == "confirm" for layout_element in current_button_elements)
        assert any(layout_element.element.action == "cancel" for layout_element in current_button_elements)
        board_tokens = headless_controller.view.layout_registry.find_elements_by_type(Token)
        has_not_gold_token = any(token.element.color != "gold" for token in board_tokens)
        assert has_not_gold_token is True
        one_not_gold_token = next(token for token in board_tokens if token.element.color != "gold")
        assert one_not_gold_token is not None
        headless_controller.current_selection.append(one_not_gold_token)
        headless_controller.view.render(headless_controller.desk, headless_controller.dialogue, headless_controller.current_action, headless_controller.current_selection)
        headless_controller.current_state = GameState.START_OF_ROUND
        action = Action(ActionType.USE_PRIVILEGE, {"token": headless_controller.current_selection[0].element, "position": headless_controller.current_selection[0].metadata["position"]})
        headless_controller.desk.apply_action(action)
        headless_controller.current_selection.clear()
        headless_controller.current_action = headless_controller.desk.get_current_action(state=headless_controller.current_state)
        headless_controller.view.render(headless_controller.desk, headless_controller.dialogue, headless_controller.current_action, headless_controller.current_selection)
        # assert one less token on the board
        board_tokens = headless_controller.view.layout_registry.find_elements_by_type(Token)
        assert len(board_tokens) == len(headless_controller.desk.board.grid) * len(headless_controller.desk.board.grid[0]) - 3 - 1
        # assert one less privilege count in player 1
        player_1_privileges = headless_controller.desk.players[0].privileges
        assert player_1_privileges == 2
        # assert one more token hold by player 1
        player_1_tokens = headless_controller.desk.players[0].tokens
        assert sum(player_1_tokens.values()) == 4
        
    
if __name__ == "__main__":
    pytest.main([__file__, "-v"])