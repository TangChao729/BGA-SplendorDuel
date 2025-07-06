import pygame
import sys
import os

# Add parent directory to path to import asset_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from view.assets import AssetManager

class AssetChecker:
    """
    Visual tool to preview and verify loaded assets.
    """
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Asset Checker - Splendor Duel")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        try:
            self.asset_manager = AssetManager()
            self.assets_loaded = True
        except Exception as e:
            print(f"Failed to load assets: {e}")
            self.assets_loaded = False
            self.error_message = str(e)
        
        self.current_view = "overview"  # overview, tokens, cards_1, cards_2, cards_3
        self.card_page = 0
    
    def run(self):
        """Main preview loop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keypress(event.key)
            
            self.screen.fill((30, 30, 40))
            
            if self.assets_loaded:
                self._render_current_view()
            else:
                self._render_error()
            
            self._render_instructions()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
    
    def _handle_keypress(self, key):
        """Handle keyboard navigation"""
        if key == pygame.K_1:
            self.current_view = "overview"
        elif key == pygame.K_2:
            self.current_view = "tokens"
        elif key == pygame.K_3:
            self.current_view = "cards_1"
        elif key == pygame.K_4:
            self.current_view = "cards_2"
        elif key == pygame.K_5:
            self.current_view = "cards_3"
        elif key == pygame.K_LEFT and "cards" in self.current_view:
            self.card_page = max(0, self.card_page - 1)
        elif key == pygame.K_RIGHT and "cards" in self.current_view:
            level = int(self.current_view.split("_")[1])
            max_pages = len(self.asset_manager.card_sprites[level]) // 10
            self.card_page = min(max_pages, self.card_page + 1)
    
    def _render_current_view(self):
        """Render the current asset view"""
        if self.current_view == "overview":
            self._render_overview()
        elif self.current_view == "tokens":
            self._render_tokens()
        elif self.current_view.startswith("cards_"):
            level = int(self.current_view.split("_")[1])
            self._render_cards(level)
    
    def _render_overview(self):
        """Show all major assets in overview"""
        y_offset = 50
        
        # Background (scaled down)
        if self.asset_manager.background:
            bg_scaled = pygame.transform.scale(self.asset_manager.background, (200, 150))
            self.screen.blit(bg_scaled, (50, y_offset))
            self._draw_text("Background", (50, y_offset + 155))

        # Bag (scaled down)
        if self.asset_manager.bag:
            bag_scaled = pygame.transform.scale(self.asset_manager.bag, (200, 150))
            self.screen.blit(bag_scaled, (250, y_offset))
            self._draw_text("Bag", (250, y_offset + 155))
        
        # Board (scaled down)
        if self.asset_manager.board:
            board_scaled = pygame.transform.scale(self.asset_manager.board, (200, 150))
            self.screen.blit(board_scaled, (500, y_offset))
            self._draw_text("Board", (500, y_offset + 155))
        
        # Sample tokens
        token_x = 50
        token_y = y_offset + 200
        for color, sprite in self.asset_manager.token_sprites.items():
            if sprite:
                self.screen.blit(sprite, (token_x, token_y))
                self._draw_text(color, (token_x, token_y + sprite.get_height() + 5))
                token_x += sprite.get_width() + 10
        
        # Other assets
        other_y = y_offset + 350
        if self.asset_manager.privilege:
            self.screen.blit(self.asset_manager.privilege, (50, other_y))
            self._draw_text("Privilege", (50, other_y + self.asset_manager.privilege.get_height() + 5))
        
        # if self.asset_manager.cards["royal"]:
        #     royal 
        #     royal_scaled = pygame.transform.scale(self.asset_manager.royal_cards, (150, 100))
        #     self.screen.blit(royal_scaled, (200, other_y))
        #     self._draw_text("Royal Cards", (200, other_y + 105))
    
    def _render_tokens(self):
        """Show all token sprites in detail"""
        self._draw_text("Token Sprites", (50, 20), large=True)
        
        x, y = 50, 80
        for color, sprite in self.asset_manager.token_sprites.items():
            if sprite:
                # Show original size and 2x scale
                self.screen.blit(sprite, (x, y))
                scaled = pygame.transform.scale(sprite, (sprite.get_width() * 2, sprite.get_height() * 2))
                self.screen.blit(scaled, (x, y + sprite.get_height() + 20))
                
                self._draw_text(f"{color}", (x, y + sprite.get_height() + scaled.get_height() + 25))
                self._draw_text(f"{sprite.get_width()}x{sprite.get_height()}", (x, y + sprite.get_height() + scaled.get_height() + 45))
                
                x += max(sprite.get_width(), scaled.get_width()) + 30
                if x > 1000:  # Wrap to next row
                    x = 50
                    y += 200
    
    def _render_cards(self, level: int):
        """Show card sprites for a specific level"""
        self._draw_text(f"Level {level} Cards (Page {self.card_page + 1})", (50, 20), large=True)
        
        cards = self.asset_manager.card_sprites[level]
        cards_per_page = 10
        start_idx = self.card_page * cards_per_page
        end_idx = min(start_idx + cards_per_page, len(cards))
        
        x, y = 50, 80
        cols = 5
        
        for i in range(start_idx, end_idx):
            card = cards[i]
            if card:
                self.screen.blit(card, (x, y))
                self._draw_text(f"Card {i}", (x, y + card.get_height() + 5))
            
            x += 120
            if (i - start_idx + 1) % cols == 0:
                x = 50
                y += 180
        
        # Show pagination info
        total_pages = (len(cards) + cards_per_page - 1) // cards_per_page
        self._draw_text(f"Total cards: {len(cards)} | Page {self.card_page + 1}/{total_pages}", (50, 700))
    
    def _render_error(self):
        """Show error message if assets failed to load"""
        self._draw_text("Failed to load assets!", (50, 50), large=True, color=(255, 100, 100))
        self._draw_text(f"Error: {self.error_message}", (50, 100), color=(255, 200, 200))
    
    def _render_instructions(self):
        """Show navigation instructions"""
        instructions = [
            "1 - Overview | 2 - Tokens | 3 - Cards L1 | 4 - Cards L2 | 5 - Cards L3",
            "← → - Navigate card pages | ESC - Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            self._draw_text(instruction, (50, 750 + i * 25), color=(200, 200, 200))
    
    def _draw_text(self, text: str, pos: tuple, large: bool = False, color: tuple = (255, 255, 255)):
        """Helper to draw text"""
        font = pygame.font.Font(None, 32 if large else 24)
        surface = font.render(text, True, color)
        self.screen.blit(surface, pos)

if __name__ == "__main__":
    checker = AssetChecker()
    checker.run()