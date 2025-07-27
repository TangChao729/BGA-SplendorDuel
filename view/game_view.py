import pygame
from typing import List, Optional, Dict, Any, Tuple, Union
import os

from model.desk import Desk
from model.actions import ActionButton
from model.game_state_machine import CurrentAction
from model.cards import Card, Deck
from model.tokens import Token
from view.assets import AssetManager
from view.layout import LayoutRegistry, LayoutElement, HSplit, VSplit, Margin

# Layout constants
MARGIN_SMALL = 5
MARGIN_MEDIUM = 10
MARGIN_LARGE = 20
PADDING = 5
BORDER_WIDTH = 2
BORDER_RADIUS_DEFAULT = 10
SCREEN_WIDTH, SCREEN_HEIGHT = 1900, 1000
MAIN_PANEL_HEIGHT = 850
DIALOGUE_HEIGHT = SCREEN_HEIGHT - MAIN_PANEL_HEIGHT
ALPHA_SEMI = 128
ALPHA_VERY_LOW = 32
FONT_SIZE_DEFAULT = 24
FONT_SIZE_TRACKER = 30

# UI constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
GRAY = (128, 128, 128)
BLUE = (0, 100, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (255, 255, 0)


def to_rect(rect: Union[Tuple[int, int, int, int], pygame.Rect]) -> pygame.Rect:
    """
    Utility to ensure a pygame.Rect is returned from either a tuple or a Rect.
    """
    if isinstance(rect, pygame.Rect):
        return rect
    else:
        return pygame.Rect(rect)


class ScaledImageCache:
    """
    Cache for scaled images to avoid recomputing them on each frame.
    """
    def __init__(self):
        self.cache: Dict[Tuple[int, int, int, int, int], pygame.Surface] = {}

    def get(self, image: pygame.Surface, width: int, height: int, margin: int) -> pygame.Surface:
        key = (id(image), width, height, margin, image.get_bitsize())
        if key not in self.cache:
            scaled = pygame.transform.scale(image, (width, height))
            self.cache[key] = scaled
        return self.cache[key]


class GameView:
    """
    Renders the game using Pygame, laying out:
      [          ] 
      [   Main   ] [Player1]
      [          ] [Player2]
    Handles all drawing and layout logic for the Splendor Duel game UI.
    """

    def __init__(self, screen: pygame.Surface, assets: AssetManager):
        self.screen = screen
        self.assets = assets
        self.font = pygame.font.SysFont(None, FONT_SIZE_DEFAULT)
        self.tracker_font = pygame.font.SysFont(None, FONT_SIZE_TRACKER)
        self.scaled_image_cache = ScaledImageCache()
        self.layout_registry = LayoutRegistry()
        # main panel
        self.view_split = HSplit(
            (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), [("main", 9), ("right", 2)]
        )

        # right panel is split into two player panels and dialogue
        self.right_split = VSplit(
            self.view_split.children["right"],
            [("player1", 1), ("player2", 1)],
        )

    def render(self, desk: Desk, dialogue: str, current_action: CurrentAction, current_selection: List[LayoutElement]) -> None:
        """
        Render the entire game view, including background, main panel, and player panels.
        """
        # Clear the layout registry at the start of each frame
        self.layout_registry.clear()
        
        self.draw_background()
        self.draw_main_panel(desk, dialogue, self.view_split.children["main"])
        self.draw_player_panel(desk.players[0], self.right_split.children["player1"])
        self.draw_player_panel(desk.players[1], self.right_split.children["player2"])
        self.draw_action_panel(desk, self.action_panel_rect, current_action)

        # highlight the selected element
        for element in current_selection:
            self._highlight_rect(element.rect)

        # highlight the current player
        if desk.current_player_index == 0:
            self._highlight_rect(self.right_split.children["player1"])
        else:
            self._highlight_rect(self.right_split.children["player2"])

        pygame.display.flip()

    def _scale_image_to_fit(
        self, image: pygame.Surface, rect: Any, margin: int = MARGIN_MEDIUM
    ) -> Any:
        """
        Scale an image to fit within a rectangle while maintaining aspect ratio.
        Returns the scaled image and its position (x, y) to center it in the rect.
        Uses a cache to avoid redundant scaling.
        """
        rect = to_rect(rect)
        img_rect = image.get_rect()

        # Calculate scale factor with margin
        available_width = rect.width - (margin * 2)
        available_height = rect.height - (margin * 2)

        scale_x = available_width / img_rect.width
        scale_y = available_height / img_rect.height
        scale = min(scale_x, scale_y)  # Use smaller scale to fit both dimensions

        # Calculate new dimensions
        new_width = max(1, int(img_rect.width * scale))
        new_height = max(1, int(img_rect.height * scale))

        # Use cache for scaled images
        scaled_image = self.scaled_image_cache.get(image, new_width, new_height, margin)

        # Calculate position to center the image in the rect
        x = rect.x + (rect.width - new_width) // 2
        y = rect.y + (rect.height - new_height) // 2

        return scaled_image, (x, y)

    def draw_background(self) -> None:
        """
        Draw the background image, scaled to the screen size.
        """
        bg = pygame.transform.scale(
            self.assets.background, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.screen.blit(bg, (0, 0))

    def draw_player_panel(self, player: Any, rect: Any) -> None:
        """
        Draw the player panel, including name, score, counters, tokens, cards, and reserved cards.
        """
        rect = Margin(rect, (MARGIN_MEDIUM, MARGIN_MEDIUM, MARGIN_MEDIUM, MARGIN_MEDIUM)).rect
        x0, y0, w, h = rect
        self._draw_boarder(rect)

        # Create a semi-transparent surface
        bg_surface = pygame.Surface((w, h))
        bg_surface.set_alpha(ALPHA_SEMI)
        bg_surface.fill(WHITE)
        self.screen.blit(bg_surface, (x0, y0))

        # Layout calculation
        player_panel = VSplit(
            (x0, y0, w, h),
            [
                ("player_name", 1),
                ("score_tracker", 2),
                ("counters", 1),
                ("tokens_sum", 2),
                ("cards_sum", 1),
                ("reserved", 3),
            ],
        )

        # Draw sub-panels
        self._draw_player_name(player, Margin(player_panel.children["player_name"], (MARGIN_SMALL,)*4).rect)
        self._draw_score_tracker(player, Margin(player_panel.children["score_tracker"], (MARGIN_SMALL,)*4).rect)
        self._draw_privilege_royal_token_counter(player, Margin(player_panel.children["counters"], (MARGIN_SMALL,)*4).rect)
        self._draw_token_area(player.tokens, Margin(player_panel.children["tokens_sum"], (MARGIN_SMALL,)*4).rect)
        self._draw_card_area(player.bonuses, Margin(player_panel.children["cards_sum"], (MARGIN_SMALL,)*4).rect)
        self._draw_reserved_cards(player.reserved, Margin(player_panel.children["reserved"], (MARGIN_SMALL,)*4).rect)

    def _draw_player_name(self, player: Any, rect: Any) -> None:
        """
        Draw the player's name in the given rectangle.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        txt = self.font.render(player.name, True, BLACK)
        self.screen.blit(txt, (rect.x + MARGIN_MEDIUM, rect.y + MARGIN_MEDIUM))

    def _draw_score_tracker(self, player: Any, rect: Any) -> None:
        """
        Draw the score tracker for the player.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        scaled_tracker, (x, y) = self._scale_image_to_fit(
            self.assets.score_tracker, rect, margin=0
        )
        self.screen.blit(scaled_tracker, (x, y))
        
        # draw player points, number of crowns, number of points from one color of cards
        split = VSplit(rect, [("upper_half", 1), ("lower_half", 1)])
        upper_half_split = HSplit(split.children["upper_half"], [("points", 1), ("crowns", 1), ("card_points", 1)])
            
        self._draw_player_points(player, upper_half_split.children["points"])
        self._draw_player_crowns(player, upper_half_split.children["crowns"])
        self._draw_player_card_points(player, upper_half_split.children["card_points"])

    def _draw_player_points(self, player: Any, rect: Any) -> None:
        """
        Draw the player's points, right-aligned in the given rectangle.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        txt = self.tracker_font.render(f"{player.points}", True, WHITE)
        txt_rect = txt.get_rect()
        # Align right with margin
        x = rect.right - txt_rect.width - MARGIN_MEDIUM
        y = rect.y + MARGIN_MEDIUM
        self.screen.blit(txt, (x, y))

    def _draw_player_crowns(self, player: Any, rect: Any) -> None:
        """
        Draw the player's crowns, centered in the given rectangle.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        txt = self.tracker_font.render(f"{player.crowns}", True, WHITE)
        txt_rect = txt.get_rect(center=rect.center)
        self.screen.blit(txt, txt_rect)

    def _draw_player_card_points(self, player: Any, rect: Any) -> None:
        """
        Draw the player's card points.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        highest_points = max(player.card_points.values())
        txt = self.tracker_font.render(f"{highest_points}", True, WHITE)
        self.screen.blit(txt, (rect.x + MARGIN_MEDIUM, rect.y + MARGIN_MEDIUM))

    def _draw_privilege_royal_token_counter(self, player: Any, rect: Any) -> None:
        """
        Draw counters for privileges, royals, and tokens.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        counter_split = HSplit(rect, [("privilege", 1), ("royal", 1), ("token", 1)])

        # Privilege counter
        scaled_privilege, (x, y) = self._scale_image_to_fit(
            self.assets.icon_privilege,
            counter_split.children["privilege"],
            margin=0,
        )
        self.screen.blit(scaled_privilege, to_rect(counter_split.children["privilege"])[:2])
        txt = self.tracker_font.render(f": {player.privileges}", True, BLACK)
        self.screen.blit(
            txt,
            (
                to_rect(counter_split.children["privilege"]).x + 32,
                to_rect(counter_split.children["privilege"]).y + 10,
            ),
        )

        # Royal cards counter
        scaled_royal_cards_stack, (x, y) = self._scale_image_to_fit(
            self.assets.icon_cards_stack_svg,
            counter_split.children["royal"],
            margin=0,
        )
        self.screen.blit(scaled_royal_cards_stack, to_rect(counter_split.children["royal"])[:2])
        txt2 = self.tracker_font.render(f": {len(player.purchased)}", True, BLACK)
        self.screen.blit(
            txt2,
            (
                to_rect(counter_split.children["royal"]).x + 40,
                to_rect(counter_split.children["royal"]).y + 10,
            ),
        )

        # Token counter
        scaled_token, (x, y) = self._scale_image_to_fit(
            self.assets.icon_plain_token,
            counter_split.children["token"],
            margin=0,
        )
        self.screen.blit(scaled_token, to_rect(counter_split.children["token"])[:2])
        txt3 = self.tracker_font.render(f": {player.get_token_count()}", True, BLACK)
        self.screen.blit(
            txt3,
            (
                to_rect(counter_split.children["token"]).x + 32,
                to_rect(counter_split.children["token"]).y + 12,
            ),
        )

    def _draw_token(self, counts: Dict[Any, int], split: Any, color: str) -> None:
        """
        Draw a single token of the given color and its count.
        """
        sclaled_token, (x, y) = self._scale_image_to_fit(
            self.assets.token_sprites[color], split.children[color], margin=MARGIN_SMALL
        )
        self.screen.blit(sclaled_token, to_rect(split.children[color])[:2])
        txt_gold = self.tracker_font.render(f":{str(counts.get(Token(color), 0))}", True, BLACK)
        self.screen.blit(
            txt_gold,
            (
                to_rect(split.children[color]).x + 35,
                to_rect(split.children[color]).y + 10,
            ),
        )

    def _draw_token_area(self, counts: Dict[Any, int], rect: Any) -> None:
        """
        Draw all tokens for a player in a grid layout.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        splits = VSplit(
            rect, [("first_row", 1), ("second_row", 1)]
        )
        first_row_split = HSplit(
            splits.children["first_row"], [("gold", 1), ("pearl", 1)]
        )
        second_row_split = HSplit(
            splits.children["second_row"],
            [("black", 1), ("blue", 1), ("red", 1), ("green", 1), ("white", 1)],
        )
        for color in ["gold", "pearl"]:
            self._draw_token(counts, first_row_split, color)
        for color in ["black", "blue", "red", "green", "white"]:
            self._draw_token(counts, second_row_split, color)

    def _draw_card_shape(self, rect: pygame.Rect, fill_color: Any = WHITE, alpha: int = ALPHA_SEMI, border_radius: int = BORDER_RADIUS_DEFAULT) -> None:
        """
        Draw a card shape with rounded corners, transparent fill, and black border.
        """
        card_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill_color_with_alpha = (*fill_color, alpha)
        pygame.draw.rect(card_surface, fill_color_with_alpha, (0, 0, rect.width, rect.height), border_radius=border_radius)
        self.screen.blit(card_surface, (rect.x, rect.y))
        pygame.draw.rect(self.screen, BLACK, rect, width=BORDER_WIDTH, border_radius=border_radius)

    def _draw_card_area(self, bonuses: Dict[Any, int], rect: Any) -> None:
        """
        Draw the player's card bonuses as colored card shapes with counts.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        split = HSplit(
            rect,
            [
                ("black", 1),
                ("blue", 1),
                ("red", 1),
                ("green", 1),
                ("white", 1),
            ]
        )
        colors = ["black", "blue", "red", "green", "white"]
        color_map = {
            "black": (0, 0, 0),
            "blue": (0, 0, 255),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "white": (255, 255, 255)
        }
        for color in colors:
            card_rect = to_rect(split.children[color])
            margin = MARGIN_SMALL
            card_rect = pygame.Rect(
                card_rect.x + margin,
                card_rect.y + margin,
                card_rect.width - 2 * margin,
                card_rect.height - 2 * margin
            )
            self._draw_card_shape(card_rect, color_map[color], alpha=ALPHA_SEMI, border_radius=8)
            bonus_count = bonuses.get(Token(color), 0)
            txt = self.font.render(str(bonus_count), True, BLACK)
            txt_rect = txt.get_rect(center=card_rect.center)
            self.screen.blit(txt, txt_rect)

    def _draw_reserved_cards(self, reserved: List[Card], rect: Union[Tuple[int, int, int, int], pygame.Rect]) -> None:
        """
        Draw the player's reserved cards in a row.
        """
        rect = to_rect(rect)
        # Draw empty slots
        for i in range(3):
            x = rect.x + i * (rect.width // 3)
            card_rect = pygame.Rect(x, rect.y, rect.width // 3 - MARGIN_SMALL, rect.height)
            self._draw_card_shape(card_rect, alpha=ALPHA_VERY_LOW)
            
        for i, card in enumerate(reserved):
            if i >= 3:  # Limit to 3 reserved cards
                break
            x = rect.x + i * (rect.width // 3)
            card_rect = pygame.Rect(x, rect.y, rect.width // 3 - MARGIN_SMALL, rect.height)
            level, index = card.id.split("-")
            card_sprite = self.assets.get_card_sprite(level=int(level), index=int(index))
            scaled_image, position = self._scale_image_to_fit(
                card_sprite, card_rect, MARGIN_SMALL
            )
            self.screen.blit(scaled_image, position)
            
            # Register the card for click detection
            self.layout_registry.register(
                f"reserved_card_{i}",
                card_rect,
                card,
                {"index": i, "card": card}
            )

    def draw_main_panel(self, desk: Desk, dialogue: str, rect: Any) -> None:
        """
        Draw the main game panel, including bag, privileges, royals, dialogue, board, and pyramid.
        """
        x0, y0, w, h = rect
        self._draw_boarder(rect)
        main_split = VSplit((x0, y0, w, h), [("action", 2),("upper", 10), ("lower", 30)])
        upper_rect = main_split.children["upper"]
        lower_rect = main_split.children["lower"]
        upper_split = HSplit(upper_rect, [("bag", 1), ("privilege", 1), ("royal", 2), ("dialogue", 2)])
        lower_split = HSplit(lower_rect, [("board", 2), ("pyramid", 3)])
        # store action panel rect
        self.action_panel_rect = main_split.children["action"]
        self._draw_bag(desk, Margin(upper_split.children["bag"], (MARGIN_MEDIUM,)*4).rect)
        self._draw_privileges(desk, Margin(upper_split.children["privilege"], (MARGIN_MEDIUM,)*4).rect)
        self._draw_royal(desk, Margin(upper_split.children["royal"], (MARGIN_MEDIUM,)*4).rect)
        self._draw_dialogue_panel(dialogue, Margin(upper_split.children["dialogue"], (MARGIN_MEDIUM,)*4).rect)
        self._draw_board(desk, Margin(lower_split.children["board"], (MARGIN_MEDIUM,)*4).rect)
        self._draw_pyramid(desk, Margin(lower_split.children["pyramid"], (MARGIN_MEDIUM,)*4).rect)

    def draw_action_panel(self, desk: Desk, rect: Any, current_action: CurrentAction) -> None:
        """
        Draw the action panel with explanation and action buttons in one horizontal line.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
        
        # Calculate total width needed for text and buttons
        txt = self.font.render(current_action.explanation, True, BLACK)
        txt_width = txt.get_width()
        
        # Calculate button widths
        button_widths = []
        button_heights = []
        for button in current_action.buttons:
            btn_txt = self.font.render(button.text, True, WHITE)
            btn_width = btn_txt.get_width() + 40
            btn_height = btn_txt.get_height() + 20
            button_widths.append(btn_width)
            button_heights.append(btn_height)
        
        # Calculate total width and spacing
        total_button_width = sum(button_widths)
        spacing = 20  # Space between elements
        total_width = txt_width + total_button_width + spacing * (len(current_action.buttons))
        
        # Calculate starting x position to center everything
        start_x = rect.centerx - total_width // 2
        current_x = start_x
        
        # Draw text
        txt_rect = txt.get_rect(midleft=(current_x, rect.centery))
        self.screen.blit(txt, txt_rect)
        current_x += txt_width + spacing
        
        # Draw buttons
        for i, button in enumerate(current_action.buttons):
            label = button.text
            btn_txt = self.font.render(label, True, WHITE)
            btn_width = button_widths[i]
            btn_height = button_heights[i]
            btn_rect = pygame.Rect(current_x, rect.centery - btn_height // 2, btn_width, btn_height)
            pygame.draw.rect(self.screen, (30, 90, 200), btn_rect, border_radius=10)
            self.screen.blit(btn_txt, btn_txt.get_rect(center=btn_rect.center))
            # Register button for click detection
            self.layout_registry.register(f"action_button_{i}", btn_rect, button, {})
            current_x += btn_width + spacing

    def _draw_bag(self, desk: Desk, rect: Any) -> None:
        """
        Draw the bag image and the number of tokens in the bag.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        scaled_bag, (x, y) = self._scale_image_to_fit(self.assets.bag, rect, margin=MARGIN_MEDIUM)
        text_height = 30
        if y + scaled_bag.get_height() + text_height > rect.bottom:
            text_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height - text_height)
            scaled_bag, (x, y) = self._scale_image_to_fit(
                self.assets.bag, text_rect, margin=MARGIN_MEDIUM
            )
        self.screen.blit(scaled_bag, (x, y))
        txt = self.font.render(f"Tokens in bag: {sum(desk.bag.counts().values())}", True, BLACK)
        self.screen.blit(txt, (rect.x + MARGIN_MEDIUM, rect.y + rect.height - text_height))

        # Register the bag for click detection
        self.layout_registry.register(
            "bag",
            pygame.Rect(x, y, scaled_bag.get_width(), scaled_bag.get_height()),
            desk.bag,
            {},
        )

    def _draw_privileges(self, desk: Desk, rect: Any) -> None:
        """
        Draw the privilege tokens in the main panel.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        split = HSplit(rect, [("privilege_1", 1), ("privilege_2", 1), ("privilege_3", 1)])
        for i in range(3):
            if i < desk.privileges:
                sub_rect = Margin(split.children[f"privilege_{i+1}"], (MARGIN_LARGE,)*4).rect
                self._draw_boarder(sub_rect)
                scaled_privilege, (x, y) = self._scale_image_to_fit(
                    self.assets.privilege, sub_rect, margin=0
                )
                self.screen.blit(scaled_privilege, (x, y))
                
                # Privilege is not clickable
                # # Register privilege for click detection
                # self.layout_registry.register(
                #     f"privilege_{i}",
                #     pygame.Rect(x, y, scaled_privilege.get_width(), scaled_privilege.get_height()),
                #     "privilege",
                #     {"index": i}
                # )

    def _draw_royal(self, desk: Desk, rect: Any) -> None:
        """
        Draw the royal cards in the main panel.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        royals = self.assets.card_sprites["royal"]
        split = HSplit(rect, [("royal_1", 1), ("royal_2", 1), ("royal_3", 1), ("royal_4", 1)])
        for i in range(4):
            if i < len(desk.royals):
                sub_rect = Margin(split.children[f"royal_{i+1}"], (MARGIN_SMALL,)*4).rect
                self._draw_boarder(sub_rect)
                scaled_royal, (x, y) = self._scale_image_to_fit(
                    self.assets.card_sprites["royal"][i], sub_rect, margin=0
                )
                self.screen.blit(scaled_royal, (x, y))
                
                # Royal card is not clickable
                # # Register royal card for click detection
                # self.layout_registry.register(
                #     f"royal_{i}",
                #     pygame.Rect(x, y, scaled_royal.get_width(), scaled_royal.get_height()),
                #     desk.royals[i],
                #     {"index": i}
                # )

    def _draw_dialogue_panel(self, text: str, rect: Any) -> None:
        """
        Draw the dialogue panel with the given text.
        """
        rect = to_rect(rect)
        pygame.draw.rect(self.screen, BLACK, rect, BORDER_WIDTH)
        txt = self.font.render(text, True, BLACK)
        self.screen.blit(txt, (rect.x + MARGIN_MEDIUM, rect.y + MARGIN_MEDIUM))

    def _draw_board(self, desk: Desk, rect: Any) -> None:
        """
        Draw the main game board, including the token grid and any tokens present.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        scaled_board, (x, y) = self._scale_image_to_fit(
            self.assets.board, rect, margin=MARGIN_MEDIUM
        )
        self.screen.blit(scaled_board, (x, y))
        split = VSplit(rect, [("reminder", 1), ("token_grid", 5)])
        self._draw_boarder(split.children["reminder"])
        self._draw_boarder(split.children["token_grid"])
        split.children["token_grid"] = Margin(split.children["token_grid"], (MARGIN_LARGE,)*4).rect
        token_grid_row_split = VSplit(split.children["token_grid"], [(f"row_{i+1}", 1) for i in range(5)])
        for row_idx in range(5):
            row_rect = token_grid_row_split.children[f"row_{row_idx+1}"]
            col_split = HSplit(row_rect, [
                (f"col_{i+1}", 1) for i in range(5)
            ])
            for col_idx in range(5):
                cell_rect = col_split.children[f"col_{col_idx+1}"]
                margin_rect = Margin(cell_rect, (MARGIN_SMALL,)*4).rect
                self._draw_boarder(margin_rect)
                token = desk.board.grid[row_idx][col_idx]
                if token is not None:
                    token_img = self.assets.token_sprites[token.color]
                    scaled_token, (tx, ty) = self._scale_image_to_fit(token_img, margin_rect, margin=0)
                    self.screen.blit(scaled_token, (tx, ty))
                    
                    # Register token for click detection
                    self.layout_registry.register(
                        f"token_{row_idx}_{col_idx}",
                        pygame.Rect(tx, ty, scaled_token.get_width(), scaled_token.get_height()),
                        token,
                        {"position": (row_idx, col_idx)}
                    )

    def _draw_pyramid(self, desk: Desk, rect: Any) -> None:
        """
        Draw the card pyramid in the main panel.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect)
        face_down = HSplit(rect, [("face_down", 1), ("face_up", 6)])
        face_down_rect = VSplit(
            face_down.children["face_down"],
            [("level_1", 1), ("level_2", 1), ("level_3", 1)],
        )
        face_up_rect = VSplit(
            face_down.children["face_up"],
            [("level_3", 1), ("level_2", 1), ("level_1", 1)],
        )
        # Draw face-down cards
        for i in range(3):
            deck: Deck = desk.pyramid.decks[i+1]
            x, y, w, h = face_down_rect.children[f"level_{i+1}"]
            card_sprite = self.assets.get_card_sprite(level=3-i, index=0)
            scaled_card, (x, y) = self._scale_image_to_fit(
                card_sprite,
                pygame.Rect(x, y, w, h),
                margin=0,
            )
            self.screen.blit(scaled_card, (x, y))
            scaled_card_width = scaled_card.get_width()

            # Register face-down card for click detection
            self.layout_registry.register(
                f"face_down_card_{i+1}",
                pygame.Rect(x, y, scaled_card.get_width(), scaled_card.get_height()),
                deck,
                {"level": 3-i, "index": 0}
            )

        # Layout for face-up cards
        def layout_face_up(level: int, count: int, y_rect: Any) -> dict:
            total_occupied_width = count * scaled_card_width + (count - 1) * MARGIN_SMALL * 2
            space_left = (y_rect[2] - total_occupied_width) // 2
            return {
                f"{i+1}": (
                    y_rect[0] + space_left + i * (scaled_card_width + MARGIN_SMALL * 2),
                    y_rect[1],
                    scaled_card_width,
                    y_rect[3],
                )
                for i in range(count)
            }
        
        def draw_face_up_card(card_amt: int, face_up_level_rects: List[pygame.Rect], level: int):
            for i in range(card_amt):
                card = desk.pyramid.slots[level][i] if i < len(desk.pyramid.slots[level]) else None
                if card is None:
                    continue
                
                # TODO: this looks messy, need to clean, why i+1?
                x, y, w, h = face_up_level_rects[f"{i+1}"]
                card_id = card.id[-2:]
                card_sprite = self.assets.get_card_sprite(level=level, index=int(card_id))
                scaled_card, (x, y) = self._scale_image_to_fit(
                    card_sprite,
                    pygame.Rect(x, y, scaled_card_width, h),
                    margin=0,
                )
                self.screen.blit(scaled_card, (x, y))
                card = desk.pyramid.slots[level][i] if i < len(desk.pyramid.slots[level]) else None
                self.layout_registry.register(
                    f"pyramid_card_{level}_{i}",
                    pygame.Rect(x, y, scaled_card.get_width(), scaled_card.get_height()),
                    card,
                    {"level": level, "index": i}
                )

        face_up_level_1 = layout_face_up(1, 5, face_up_rect.children["level_1"])
        draw_face_up_card(5, face_up_level_1, 1)
        face_up_level_2 = layout_face_up(2, 4, face_up_rect.children["level_2"])
        draw_face_up_card(4, face_up_level_2, 2)
        face_up_level_3 = layout_face_up(3, 3, face_up_rect.children["level_3"])
        draw_face_up_card(3, face_up_level_3, 3)


    def _draw_boarder(self, rect: Any, highlight: Any = BLACK) -> None:
        """
        Draw a border around the given rectangle.
        Accepts either a tuple or pygame.Rect.
        """
        rect = to_rect(rect)
        pygame.draw.rect(self.screen, highlight, rect, BORDER_WIDTH)

    
    def _highlight_rect(self, rect: Any, alpha: int = 50) -> None:
        """
        Draw a semi-transparent yellow highlight over the given rectangle.
        """
        rect = to_rect(rect)
        self._draw_boarder(rect, highlight=(255, 255, 0))
        highlight_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        highlight_surface.fill((255, 255, 0, alpha))
        self.screen.blit(highlight_surface, (rect.x, rect.y))
