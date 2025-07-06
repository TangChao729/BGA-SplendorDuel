import os
import pygame


class AssetManager:
    """
    Loads and manages all graphical assets (images and sprite sheets) for Splendor Duel.

    Attributes:
        background (Surface): Background image.
        board (Surface): Board background.
        token_sprites (Dict[str, Surface]): Token images keyed by color.
        card_sprites (Dict[int, List[Surface]]): Card images per level.
        privilege (Surface): Privilege scroll icon.
        royal_cards (Surface): Royal cards image.
        score_tile (Surface): Score tile image.
    """

    def __init__(self, base_path: str = "./data/images"):
        self.base_path = base_path
        # Loaded assets:
        self.background = None
        self.board = None
        self.token_sprites = {}
        self.card_sprites = {1: [], 2: [], 3: [], "royal": []}
        self.privilege = None
        self.score_tile = None
        
        self._load_all()

    def _load_image(self, filename: str) -> pygame.Surface:
        path = os.path.join(self.base_path, filename)
        image = pygame.image.load(path).convert_alpha()
        return image

    def _load_spritesheet(
        self, filename: str, tile_width: int, tile_height: int
    ) -> list[pygame.Surface]:
        """
        Slice a sprite sheet into individual tiles.
        """
        sheet = self._load_image(filename)
        rect = sheet.get_rect()
        sprites = []
        for y in range(0, rect.height, tile_height):
            for x in range(0, rect.width, tile_width):
                # subsurface returns a view
                sprite = sheet.subsurface(pygame.Rect(x, y, tile_width, tile_height))
                sprites.append(sprite)
        return sprites

    def _load_all(self) -> None:
        # Backgrounds
        self.background = self._load_image("background.jpg")
        
        # Bag
        self.bag = self._load_image("bag.png")

        # Board
        self.board = self._load_image("board.jpg")

        # Cards: three separate sheets
        for level, fname in zip((1,2,3), ("cards1.jpg","cards2.jpg","cards3.jpg")):
            # you may need to adjust cols/rows based on your sheet
            if level == 1:
                cols = 31
            elif level == 2:
                cols = 25
            else:
                cols = 14
            sheet = self._load_image(fname)
            rect = sheet.get_rect()
            rows = 1
            tile_w = rect.width // cols
            tile_h = rect.height // rows
            self.card_sprites[level] = self._load_spritesheet(fname, tile_w, tile_h)

        # Privilege scroll
        self.privilege = self._load_image("privilege.png")
    
        # royal cards:
        royal_sheet = self._load_image("royal-cards.jpg")
        w, h = royal_sheet.get_rect().size
        tile_w = w // 4
        tile_h = h
        for idx in range(4):
            rect = pygame.Rect(idx * tile_w, 0, tile_w, tile_h)
            self.card_sprites["royal"].append(royal_sheet.subsurface(rect))

        # Score tile
        self.score_tile = self._load_image("score-tile.jpg")

        # Score tracker
        self.score_tracker = self._load_image("score-tile-playerboard.jpg")

        # Tokens
        token_sheet = self._load_image("tokens.png")
        w, h = token_sheet.get_rect().size
        tile_w = w // 8
        tile_h = h
        colors = ["gold", "pearl", "blue", "white", "green", "black", "red", "wild"]
        for idx, color in enumerate(colors):
            rect = pygame.Rect(idx * tile_w, 0, tile_w, tile_h)
            self.token_sprites[color] = token_sheet.subsurface(rect)

        # Icons
        icon_sheet = self._load_image("icons.png")
        w, h = icon_sheet.get_rect().size
        tile_w = w // 5
        tile_h = h
        icons = ["red_velvet", "crown", "cards_stack", "privilege", "plain_token"]
        for idx, icon in enumerate(icons):
            rect = pygame.Rect(idx * tile_w, 0, tile_w, tile_h)
            setattr(self, "icon_" + icon, icon_sheet.subsurface(rect))

        # Cards svg icon
        self.icon_cards_stack_svg = self._load_image("cards.svg")

if __name__ == "__main__":
    # Example usage
    pygame.init()
    pygame.display.set_mode((1,1))
    asset_manager = AssetManager()
    print("Assets loaded successfully!")
    # You can now use asset_manager.background, asset_manager.token_sprites, etc.
    pygame.quit()