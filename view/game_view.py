import pygame
from typing import Dict, List, Tuple, Any
from view.layout import HSplit, VSplit, Margin

from model.desk import Desk
from view.assets import AssetManager

# Layout constants
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 1000
MAIN_PANEL_HEIGHT = 850
DIALOGUE_HEIGHT = SCREEN_HEIGHT - MAIN_PANEL_HEIGHT

# Colors
WHITE = (255, 255, 255)  # Semi-transparent white for backgrounds
BLACK = (0, 0, 0)
RED = (255, 0, 0)


class GameView:
    """
    Renders the game using Pygame, laying out:
      [          ] [Player1]
      [   Main   ] [Player2]
      [          ] 
    """

    def __init__(self, screen: pygame.Surface, assets: AssetManager):
        self.screen = screen
        self.assets = assets
        self.font = pygame.font.SysFont(None, 24)
        self.tracker_font = pygame.font.SysFont(None, 30)
        

        # main panel
        self.view_split = HSplit(
            (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), [("main", 9), ("right", 2)]
        )

        # right panel is split into two player panels and dialogue
        self.right_split = VSplit(
            self.view_split.children["right"],
            [("player1", 1), ("player2", 1)],
        )

    def render(self, desk: Desk, dialogue: str = "") -> None:
        self.draw_background()
        self.draw_main_panel(desk, dialogue, self.view_split.children["main"])
        self.draw_player_panel(desk.players[0], self.right_split.children["player1"])
        self.draw_player_panel(desk.players[1], self.right_split.children["player2"])
        pygame.display.flip()

    def _scale_image_to_fit(
        self, image: pygame.Surface, rect: pygame.Rect, margin: int = 10
    ) -> Tuple[pygame.Surface, Tuple[int, int]]:
        """
        Scale an image to fit within a rectangle while maintaining aspect ratio.
        Returns the scaled image and its position (x, y) to center it in the rect.
        """
        img_rect = image.get_rect()

        # Calculate scale factor with margin
        available_width = rect.width - (margin * 2)
        available_height = rect.height - (margin * 2)

        scale_x = available_width / img_rect.width
        scale_y = available_height / img_rect.height
        scale = min(scale_x, scale_y)  # Use smaller scale to fit both dimensions

        # Calculate new dimensions
        new_width = int(img_rect.width * scale)
        new_height = int(img_rect.height * scale)

        # Scale the image
        scaled_image = pygame.transform.scale(image, (new_width, new_height))

        # Calculate position to center the image in the rect
        x = rect.x + (rect.width - new_width) // 2
        y = rect.y + (rect.height - new_height) // 2

        return scaled_image, (x, y)

    def draw_background(self) -> None:
        bg = pygame.transform.scale(
            self.assets.background, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.screen.blit(bg, (0, 0))

    def draw_player_panel(self, player, rect: Tuple[int, int, int, int]) -> None:
        rect = Margin(rect, (10, 10, 10, 10)).rect
        x0, y0, w, h = rect
        self._draw_boarder(rect)
        # add margin to the panel
        

        # Create a semi-transparent surface
        bg_surface = pygame.Surface((w, h))
        bg_surface.set_alpha(128)  # 50% transparency (0-255)
        bg_surface.fill(WHITE)
        self.screen.blit(bg_surface, (x0, y0))

        # slice the panel into sub‐areas
        """
        [player name]
        [score tracker]
        [privileges + royals + gem counter]
        [tokens sum]
        [cards sum]
        """

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

        # Draw privileges and royals
        # Player name
        name_rect = pygame.Rect(
            *Margin(player_panel.children["player_name"], (5, 5, 5, 5)).rect
        )
        self._draw_player_name(player, name_rect)

        # Score tracker
        score_rect = pygame.Rect(
            *Margin(player_panel.children["score_tracker"], (5, 5, 5, 5)).rect
        )
        self._draw_score_tracker(player, score_rect)

        # Counters (privileges + royals + gem counter)
        counters_rect = pygame.Rect(
            *Margin(player_panel.children["counters"], (5, 5, 5, 5)).rect
        )
        self._draw_privilege_royal_token_counter(player, counters_rect)

        # Tokens sum
        tokens_rect = pygame.Rect(
            *Margin(player_panel.children["tokens_sum"], (5, 5, 5, 5)).rect
        )
        self._draw_token_area(player.tokens, tokens_rect)

        # Cards sum
        cards_rect = pygame.Rect(
            *Margin(player_panel.children["cards_sum"], (5, 5, 5, 5)).rect
        )
        self._draw_card_area(player.bonuses, cards_rect)

        # Reserved cards
        reserved_rect = pygame.Rect(
            *Margin(player_panel.children["reserved"], (5, 5, 5, 5)).rect
        )
        self._draw_reserved_cards(player.reserved, reserved_rect)

    def _draw_player_name(self, player, rect: pygame.Rect) -> None:
        self._draw_boarder(rect)
        # Player name
        txt = self.font.render(player.name, True, BLACK)
        self.screen.blit(txt, (rect.x + 10, rect.y + 10))

    def _draw_score_tracker(self, player, rect: pygame.Rect) -> None:
        self._draw_boarder(rect)
        # Score tracker
        scaled_tracker, (x, y) = self._scale_image_to_fit(
            self.assets.score_tracker, rect, margin=0
        )
        self.screen.blit(scaled_tracker, (x, y))
        #TODO: draw player points and crowns

    def _draw_privilege_royal_token_counter(self, player, rect: pygame.Rect) -> None:
        self._draw_boarder(rect)

        counter_split = HSplit(rect, [("privilege", 1), ("royal", 1), ("token", 1)])

        # Privilege counter
        scaled_privilege, (x, y) = self._scale_image_to_fit(
            self.assets.icon_privilege,
            pygame.Rect(*counter_split.children["privilege"]),
            margin=0,
        )
        self.screen.blit(scaled_privilege, counter_split.children["privilege"][:2])
        txt = self.tracker_font.render(f": {player.privileges}", True, BLACK)
        self.screen.blit(
            txt,
            (
                counter_split.children["privilege"][0] + 32,
                counter_split.children["privilege"][1] + 10,
            ),
        )

        # Royal cards counter
        scaled_royal_cards_stack, (x, y) = self._scale_image_to_fit(
            self.assets.icon_cards_stack_svg,
            pygame.Rect(*counter_split.children["royal"]),
            margin=0,
        )
        self.screen.blit(scaled_royal_cards_stack, counter_split.children["royal"][:2])
        txt2 = self.tracker_font.render(f": {len(player.purchased)}", True, BLACK)
        self.screen.blit(
            txt2,
            (
                counter_split.children["royal"][0] + 40,
                counter_split.children["royal"][1] + 10,
            ),
        )

        # Token counter
        scaled_token, (x, y) = self._scale_image_to_fit(
            self.assets.icon_plain_token,
            pygame.Rect(*counter_split.children["token"]),
            margin=0,
        )
        self.screen.blit(scaled_token, counter_split.children["token"][:2])
        txt3 = self.tracker_font.render(f": {player.get_token_count()}", True, BLACK)
        self.screen.blit(
            txt3,
            (
                counter_split.children["token"][0] + 32,
                counter_split.children["token"][1] + 12,
            ),
        )

    def _draw_token(self, counts: Dict[str, int], split, color: str) -> None:
        # Draw gold and pearl tokens
        sclaled_token, (x, y) = self._scale_image_to_fit(
            self.assets.token_sprites[color], pygame.Rect(split.children[color]), margin=5
        )
        self.screen.blit(sclaled_token, split.children[color][:2])
        txt_gold = self.tracker_font.render(f":{str(counts.get(color, 0))}", True, BLACK)
        self.screen.blit(
            txt_gold,
            (
                split.children[color][0] + 35,
                split.children[color][1] + 10,
            ),  
        )

    def _draw_token_area(self, counts: Dict[str, int], rect: pygame.Rect) -> None:
        self._draw_boarder(rect)
        # Draw tokens in a row
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

        self._draw_token(counts, first_row_split, "gold")
        self._draw_token(counts, first_row_split, "pearl")
        self._draw_token(counts, second_row_split, "black")
        self._draw_token(counts, second_row_split, "blue")
        self._draw_token(counts, second_row_split, "red")
        self._draw_token(counts, second_row_split, "green")
        self._draw_token(counts, second_row_split, "white")

    def _draw_card_shape(self, rect: pygame.Rect, fill_color: Tuple[int, int, int] = (255, 255, 255), alpha: int = 128, border_radius: int = 10) -> None:
        """
        Draw a card shape with rounded corners, transparent fill, and black border.
        
        Args:
            rect: Rectangle defining the card position and size
            fill_color: RGB color for the card fill (default: white)
            alpha: Transparency level 0-255 (default: 128 = 50% transparent)
            border_radius: Corner radius in pixels (default: 10)
        """
        # Create a temporary surface for the transparent fill
        card_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Fill with transparent color
        fill_color_with_alpha = (*fill_color, alpha)
        pygame.draw.rect(card_surface, fill_color_with_alpha, (0, 0, rect.width, rect.height), border_radius=border_radius)
        
        # Blit the transparent surface to the main screen
        self.screen.blit(card_surface, (rect.x, rect.y))
        
        # Draw the black border on top
        pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=border_radius)

    def _draw_card_area(self, bonuses: Dict[str, int], rect: pygame.Rect) -> None:
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

        # Draw card shapes for each color
        colors = ["black", "blue", "red", "green", "white"]
        color_map = {
            "black": (0, 0, 0),
            "blue": (0, 0, 255),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "white": (255, 255, 255)
        }
        for color in colors:
            card_rect = pygame.Rect(*split.children[color])
            # Add margin to the card
            margin = 5
            card_rect = pygame.Rect(
                card_rect.x + margin,
                card_rect.y + margin,
                card_rect.width - 2 * margin,
                card_rect.height - 2 * margin
            )
            
            # Draw the card shape with color-specific fill
            self._draw_card_shape(card_rect, color_map[color], alpha=128, border_radius=8)
            
            # Draw the bonus count on the card
            bonus_count = bonuses.get(color, 0)
            txt = self.font.render(str(bonus_count), True, BLACK)
            txt_rect = txt.get_rect(center=card_rect.center)
            self.screen.blit(txt, txt_rect)

    def _draw_reserved_cards(self, reserved: List[Any], rect: pygame.Rect) -> None:
        self._draw_boarder(rect)
        # Draw reserved cards in a row
        if not reserved:
            return
        
        split = HSplit(
            rect,
            [("card1", 1), ("card2", 1), ("card3", 1)]
        )

        for i, card in enumerate(reserved):
            if i >= 3:
                break
            card_rect = pygame.Rect(*split.children[f"card{i+1}"])
            scaled_card, (x, y) = self._scale_image_to_fit(
                self.assets.card_sprites[1][10],
                card_rect,
                margin=5
            )
            self.screen.blit(scaled_card, (x, y))

    def draw_main_panel(self, desk: Desk, dialogue: str, rect: Tuple[int, int, int, int]) -> None:
        x0, y0, w, h = rect
        self._draw_boarder(rect)

        # 1) build the top‐level vertical split
        main_split = VSplit((x0, y0, w, h), [("upper", 1), ("lower", 3)])

        # 2) grab the exact rectangles it computed
        upper_rect = main_split.children["upper"]
        lower_rect = main_split.children["lower"]

        # 3) feed those straight into your HSplit calls
        upper_split = HSplit(upper_rect, [("bag", 1), ("privilege", 1), ("royal", 2), ("dialogue", 2)])

        lower_split = HSplit(lower_rect, [("board", 2), ("pyramid", 3)])

        # Draw upper row: bag, privilege, royal
        bag_rect = pygame.Rect(
            *Margin(upper_split.children["bag"], (10, 10, 10, 10)).rect
        )
        self._draw_bag(desk, bag_rect)

        priv_rect = pygame.Rect(
            *Margin(upper_split.children["privilege"], (10, 10, 10, 10)).rect
        )
        self._draw_privileges(desk, priv_rect)

        royal_rect = pygame.Rect(
            *Margin(upper_split.children["royal"], (10, 10, 10, 10)).rect
        )
        self._draw_royal(desk, royal_rect)

        dialogue_rect = pygame.Rect(
            *Margin(upper_split.children["dialogue"], (10, 10, 10, 10)).rect
        )
        self._draw_dialogue_panel(dialogue, dialogue_rect)

        # Draw lower row: board, pyramid
        board_rect = pygame.Rect(
            *Margin(lower_split.children["board"], (10, 10, 10, 10)).rect
        )
        self._draw_board(desk, board_rect)

        pyramid_rect = pygame.Rect(
            *Margin(lower_split.children["pyramid"], (10, 10, 10, 10)).rect
        )
        self._draw_pyramid(desk, pyramid_rect)

    def _draw_bag(self, desk: Desk, rect: pygame.Rect) -> None:
        self._draw_boarder(rect)

        # Scale and center the bag image
        scaled_bag, (x, y) = self._scale_image_to_fit(self.assets.bag, rect, margin=10)

        # Reserve space for text at bottom
        text_height = 30
        if y + scaled_bag.get_height() + text_height > rect.bottom:
            # Recalculate with text space reserved
            text_rect = pygame.Rect(
                rect.x, rect.y, rect.width, rect.height - text_height
            )
            scaled_bag, (x, y) = self._scale_image_to_fit(
                self.assets.bag, text_rect, margin=10
            )

        self.screen.blit(scaled_bag, (x, y))

        # Draw text at bottom
        txt = self.font.render(f"Tokens in bag: {sum(desk.bag.counts().values())}", True, BLACK)
        self.screen.blit(txt, (rect.x + 10, rect.y + rect.height - 30))

    def _draw_privileges(self, desk: Desk, rect: pygame.Rect) -> None:
        self._draw_boarder(rect)
        split = HSplit(rect, [("privilege_1", 1), ("privilege_2", 1), ("privilege_3", 1)])
        for i in range(3):
        # Use *Margin to draw margin on each rect, and within each rect draw privilege
            if i < desk.privileges:
                sub_rect = Margin(split.children[f"privilege_{i+1}"], (20, 20, 20, 20)).rect
                self._draw_boarder(sub_rect)
                # x = sub_rect[0] + (sub_rect[2] - self.assets.privilege.get_width()) // 2
                # y = sub_rect[1] + (sub_rect[3] - self.assets.privilege.get_height()) // 2
                scaled_privilege, (x, y) = self._scale_image_to_fit(
                    self.assets.privilege, pygame.Rect(sub_rect), margin=0
                )
                self.screen.blit(scaled_privilege, (x, y))


    def _draw_royal(self, desk: Desk, rect: pygame.Rect) -> None:
        self._draw_boarder(rect)
        royals = self.assets.card_sprites["royal"]

        split = HSplit(rect, [("royal_1", 1), ("royal_2", 1), ("royal_3", 1), ("royal_4", 1)])
        for i in range(4):
            if i < len(desk.royals):
                sub_rect = Margin(split.children[f"royal_{i+1}"], (5, 5, 5, 5)).rect
                self._draw_boarder(sub_rect)
                scaled_royal, (x, y) = self._scale_image_to_fit(
                    self.assets.card_sprites["royal"][i], pygame.Rect(sub_rect), margin=0
                )
                self.screen.blit(scaled_royal, (x, y))

    def _draw_dialogue_panel(self, text: str, rect: Tuple[int, int, int, int]) -> None:
        pygame.draw.rect(self.screen, BLACK, rect, 2)
        txt = self.font.render(text, True, BLACK)
        self.screen.blit(txt, (rect[0] + 10, rect[1] + 10))

    def _draw_board(self, desk: Desk, rect: pygame.Rect) -> None:
        self._draw_boarder(rect)
        # scale
        scaled_board, (x, y) = self._scale_image_to_fit(
            self.assets.board, rect, margin=10
        )
        # draw the scaled board image
        self.screen.blit(scaled_board, (x, y))
        # TODO: draw the grid based on the board size
        split = VSplit(rect, [("reminder", 1), ("token_grid", 5)])
        self._draw_boarder(split.children["reminder"])
        self._draw_boarder(split.children["token_grid"])
        split.children["token_grid"] = Margin(split.children["token_grid"], (20, 20, 20, 20)).rect
        # divide the token grid into 5 rows * 5 columns
        token_grid_row_split = HSplit(split.children["token_grid"], [("row_1", 1), ("row_2", 1), ("row_3", 1), ("row_4", 1), ("row_5", 1)])
        for row_idx in range(5):
            row_rect = token_grid_row_split.children[f"row_{row_idx+1}"]
            # Split this row into 5 columns
            col_split = VSplit(row_rect, [
                (f"col_1", 1),
                (f"col_2", 1),
                (f"col_3", 1),
                (f"col_4", 1),
                (f"col_5", 1),
            ])
            for col_idx in range(5):
                cell_rect = col_split.children[f"col_{col_idx+1}"]
                # Apply margin to the cell
                margin_rect = Margin(cell_rect, (5, 5, 5, 5)).rect
                # Draw the border for the cell
                self._draw_boarder(margin_rect)
                # Draw the token if present
                token = desk.board.grid[row_idx][col_idx]
                if token is not None:
                    # Assume token has a .color attribute and self.assets.token_images dict
                    token_img = self.assets.token_sprites[token.color]
                    scaled_token, (tx, ty) = self._scale_image_to_fit(token_img, pygame.Rect(margin_rect), margin=0)
                    self.screen.blit(scaled_token, (tx, ty))

        

    def _draw_pyramid(self, desk: Desk, rect: pygame.Rect) -> None:
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
            x, y, w, h = face_down_rect.children[f"level_{i+1}"]
            # pygame.draw.rect(self.screen, BLACK, face_down_rect.children[f"level_{i+1}"], 1)
            scaled_card, (x, y) = self._scale_image_to_fit(
                self.assets.card_sprites[3 - i][0],
                pygame.Rect(face_down_rect.children[f"level_{i+1}"]),
                margin=0,
            )
            self.screen.blit(scaled_card, (x, y))
            scaled_card_width = scaled_card.get_width()

        # face_up_level_1 = HSplit(
        #     face_up_rect.children["level_1"],
        #     [("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1)]
        # )
        face_up_level_1 = {}
        total_occupied_width = 5 * scaled_card_width + 4 * 10  # margin
        space_left = (face_up_rect.children["level_1"][2] - total_occupied_width) // 2
        for i in range(5):
            # Calculate the x position with space left
            x = (
                face_up_rect.children["level_1"][0]
                + space_left
                + i * (scaled_card_width + 10)
            )
            y = face_up_rect.children["level_1"][1]
            w = scaled_card_width
            h = face_up_rect.children["level_1"][3]
            face_up_level_1[f"{i+1}"] = (x, y, w, h)

        for i in range(5):
            x, y, w, h = face_up_level_1[f"{i+1}"]
            scaled_card, (x, y) = self._scale_image_to_fit(
                self.assets.card_sprites[1][i + 1],
                pygame.Rect(x, y, scaled_card_width, h),
                margin=0,
            )
            # Draw the scaled card image
            self.screen.blit(scaled_card, (x, y))
            # self.screen.blit(self.assets.card_sprites[1][i], (x + 10, y + 10))

        # face_up_level_2 = HSplit(
        #     face_up_rect.children["level_2"],
        #     [("1", 1), ("2", 1), ("3", 1), ("4", 1)]
        # )
        face_up_level_2 = {}
        total_occupied_width = 4 * scaled_card_width + 3 * 10  # margin
        space_left = (face_up_rect.children["level_2"][2] - total_occupied_width) // 2
        for i in range(4):
            # Calculate the x position with space left
            x = (
                face_up_rect.children["level_2"][0]
                + space_left
                + i * (scaled_card_width + 10)
            )
            y = face_up_rect.children["level_2"][1]
            w = scaled_card_width
            h = face_up_rect.children["level_2"][3]
            face_up_level_2[f"{i+1}"] = (x, y, w, h)

        for i in range(4):
            x, y, w, h = face_up_level_2[f"{i+1}"]
            scaled_card, (x, y) = self._scale_image_to_fit(
                self.assets.card_sprites[2][i + 1],
                pygame.Rect(x, y, scaled_card_width, h),
                margin=0,
            )
            # Draw the scaled card image
            self.screen.blit(scaled_card, (x, y))

        # face_up_level_3 = HSplit(
        #     face_up_rect.children["level_3"],
        #     [("1", 1), ("2", 1), ("3", 1)]
        # )

        face_up_level_3 = {}
        total_occupied_width = 3 * scaled_card_width + 2 * 10  # margin
        space_left = (face_up_rect.children["level_3"][2] - total_occupied_width) // 2
        for i in range(3):
            # Calculate the x position with space left
            x = (
                face_up_rect.children["level_3"][0]
                + space_left
                + i * (scaled_card_width + 10)
            )
            y = face_up_rect.children["level_3"][1]
            w = scaled_card_width
            h = face_up_rect.children["level_3"][3]
            face_up_level_3[f"{i+1}"] = (x, y, w, h)

        for i in range(3):
            x, y, w, h = face_up_level_3[f"{i+1}"]
            scaled_card, (x, y) = self._scale_image_to_fit(
                self.assets.card_sprites[3][i + 1],
                pygame.Rect(x, y, scaled_card_width, h),
                margin=0,
            )
            # Draw the scaled card image
            self.screen.blit(scaled_card, (x, y))


    def _draw_boarder(self, rect: Tuple[int, int, int, int]) -> None:
        """
        Draw a border around the given rectangle.
        """
        x0, y0, w, h = rect
        panel_rect = pygame.Rect(x0, y0, w, h)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)

    def _draw_boarder(self, rect: pygame.Rect, highlight=BLACK) -> None:
        """
        Draw a border around the given rectangle.
        """
        pygame.draw.rect(self.screen, highlight, rect, 2)
