import json
import random
from typing import Dict, List, Optional, Tuple, Any
random.seed(42)  # For reproducibility in tests
from model.piece import Piece

def _symbol(color: str) -> str:
    # map token colors to display symbols or color names
    symbol_map = {
        "black": "⚫",
        "red": "🔴",
        "green": "🟢",
        "blue": "🔵",
        "white": "⚪",
        "pearl": "🟣",  
        "gold": "🟡",  
    }
    return symbol_map.get(color, color)


class Token(Piece):
    """
    Represents a single token unit in Splendor Duel.

    Attributes:
        color (str): One of "black", "red", "green", "blue", "white", "pearl", or "gold".
    """

    def __init__(self, color: str):
        super().__init__(color)
        self.color = color

    def to_dict(self) -> Dict[str, Any]:
        return {"color": self.color}

    def __repr__(self) -> str:
        return f"<Token {self.color}:{_symbol(self.color)}>"


class Bag(Piece):
    """
    Holds all tokens available to seed and refill the board.

    Responsibilities:
        - Initialize with counts per color.
        - draw(): shuffle and return all tokens, emptying the bag.
        - return_tokens(tokens): append returned tokens.
        - counts(): current counts of tokens.
    """

    def __init__(self, initial_counts: Dict[Token, int]):
        """
        Args:
            initial_counts: map from token color to starting count.
        """
        super().__init__("bag")
        self._tokens: List[Token] = []
        for token, count in initial_counts.items():
            for _ in range(count):
                self._tokens.append(token)

    @classmethod
    def from_json(cls, path: str) -> "Bag":
        """
        Load initial token counts from a JSON file mapping color->count.
        """
        with open(path, "r", encoding="utf-8") as f:
            counts = json.load(f)
        return cls(counts)

    def __repr__(self) -> str:
        counts = self.counts()
        total = len(self._tokens)
        return f"<Bag counts={counts} total={total}>"

    def draw(self, shuffle=True) -> List[Token]:
        """
        Shuffle and return all tokens (of any color) from the bag, emptying it.
        """
        if shuffle:
            random.shuffle(self._tokens)
        drawn = self._tokens.copy()
        self._tokens.clear()
        return drawn

    def return_tokens(self, tokens: List[Token]) -> None:
        """
        Return tokens back into the bag (no shuffle).
        """
        self._tokens.extend(tokens)

    def counts(self) -> Dict[Token, int]:
        """
        Current counts of tokens by color.
        """
        ctr: Dict[Token, int] = {}
        for t in self._tokens:
            ctr[t] = ctr.get(t, 0) + 1
        return ctr

    def is_empty(self) -> bool:
        """
        Check if the bag is empty.
        """
        return not self._tokens

    def __len__(self) -> int:
        return len(self._tokens)


class Board(Piece):
    """
    Represents the board as a 5×5 grid of tokens drawn from the bag.

    Responsibilities:
        - Fill grid in a spiral order from center outward.
        - Compute eligible draw combinations for gem/pearl lines or single wildcard 'gold'.
        - Draw tokens by combination, validating eligibility.
    """

    def __init__(self, rows: int = 5, cols: int = 5):
        super().__init__("board")
        self.rows = rows
        self.cols = cols
        self.grid: List[List[Optional[Token]]] = [[None] * cols for _ in range(rows)]
        self._spiral_coords = self._compute_spiral_coords()
        

    def _compute_spiral_coords(self) -> List[Tuple[int, int]]:
        """
        Generate grid coordinates in a spiral starting from center, moving down first, rotating clockwise.
        """
        coords: List[Tuple[int, int]] = []
        center_r, center_c = self.rows // 2, self.cols // 2
        r, c = center_r, center_c
        coords.append((r, c))
        directions = [(1, 0), (0, -1), (-1, 0), (0, 1)]  # down, right, up, left
        step_size = 1
        dir_idx = 0
        while len(coords) < self.rows * self.cols:
            for _ in range(2):
                dr, dc = directions[dir_idx % 4]
                for _ in range(step_size):
                    if len(coords) >= self.rows * self.cols:
                        break
                    r += dr; c += dc
                    if 0 <= r < self.rows and 0 <= c < self.cols:
                        coords.append((r, c))
                dir_idx += 1
            step_size += 1
        return coords

    def fill_grid(self, tokens: List[Token]) -> None:
        """
        Fill the grid by drawing all tokens from the bag and placing them along the spiral coords.
        """
        if len(tokens) > self.rows * self.cols:
            raise ValueError("Too many tokens to fit on the board")
        elif len(tokens) < 0:
            raise ValueError("Cannot fill grid with negative number of tokens")
        else:
            for (r, c), token in zip(self._spiral_coords, tokens):
                self.grid[r][c] = token

    def privileges_draws(self) -> List[Dict[str, List[Tuple[int, int]]]]:
        """
        Return a list of tokens that can be drawn using privileges.
        - Any token other than 'gold' can be drawn.
        """
        tokens: List[Dict[str, List[Tuple[int, int]]]] = []
        for r in range(self.rows):
            for c in range(self.cols):
                t = self.grid[r][c]
                if t and t.color != "gold":
                    dm: Dict[str, List[Tuple[int, int]]] = {t.color: [(r, c)]}
                    if dm not in tokens:
                        tokens.append(dm)
        return tokens

    def eligible_draws(self) -> List[Dict[str, List[Tuple[int, int]]]]:
        """
        Compute all legal token combinations for a TAKE_TOKENS action:
        - Up to 3 adjacent gem or 'pearl' tokens (no 'gold'), in straight lines.
        - Or take exactly 1 'gold' token.

        Returns:
            List of dicts mapping color -> list of (row,col) coords.
        """
        combos: List[Dict[str, List[Tuple[int, int]]]] = []
        # gem and pearl combos (color != gold)
        for r in range(self.rows):
            for c in range(self.cols):
                start = self.grid[r][c]
                if start and start.color != "gold":
                    for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
                        path: List[Tuple[int,int]] = []
                        rr, cc = r, c
                        for _ in range(3):
                            if 0 <= rr < self.rows and 0 <= cc < self.cols:
                                t = self.grid[rr][cc]
                                if t and t.color != "gold":
                                    path.append((rr,cc))
                                    for L in range(1, len(path)+1):
                                        sub = path[:L]
                                        dm: Dict[str,List[Tuple[int,int]]] = {}
                                        for (rr2,cc2) in sub:
                                            colr = self.grid[rr2][cc2].color
                                            dm.setdefault(colr, []).append((rr2,cc2))
                                        if dm not in combos:
                                            combos.append(dm)
                                else:
                                    break
                            rr += dr; cc += dc
        # single gold
        for r in range(self.rows):
            for c in range(self.cols):
                t = self.grid[r][c]
                if t and t.color == "gold":
                    dm = {"gold": [(r,c)]}
                    if dm not in combos:
                        combos.append(dm)

        self.eligible_draws_cache = combos
        return combos

    def draw_tokens(self, combo: Dict[str, List[Tuple[int, int]]]) -> List[Token]:
        """
        Execute a draw action if combo is eligible; remove tokens from grid and return them.
        Raises ValueError if combo not eligible.
        """
        if not hasattr(self, 'eligible_draws_cache'):
            self.eligible_draws()
        if combo not in self.eligible_draws_cache:
            raise ValueError("Invalid draw combination")
        drawn: List[Token] = []
        for color, coords in combo.items():
            for (r, c) in coords:
                t = self.grid[r][c]
                if t and t.color == color:
                    drawn.append(t)
                    self.grid[r][c] = None
        return drawn

    def to_dict(self) -> List[List[Optional[Dict[str,Any]]]]:
        return [[t.to_dict() if t else None for t in row] for row in self.grid]

    def counts(self) -> Dict[Token, int]:
        """
        Count tokens currently on board.
        """
        ctr: Dict[Token,int] = {}
        for row in self.grid:
            for t in row:
                if t:
                    ctr[t] = ctr.get(t, 0) + 1
        return ctr

    def __repr__(self) -> str:
        rows_repr: List[str] = ["Board"]
        for row in self.grid:
            rows_repr.append("[" + " ".join(_symbol(t.color) if t else "__" for t in row) + "]")
        return "\n".join(rows_repr)

if __name__ == "__main__":
    # Example usage
    initial_counts = {
        Token("black"): 1,
        Token("red"): 1,
        Token("blue"): 1,
        Token("green"): 1,
        Token("white"): 1,
        Token("pearl"): 1,
        # "gold": 1,  # Wildcard tokens
    }
    bag = Bag(initial_counts)
    board = Board()
    tokens = bag.draw()
    board.fill_grid(tokens)
    print("Initial board:")
    print(board)
    eligible = board.eligible_draws()
    print("Eligible draws:", eligible)
    print("Length of eligible draws:", len(eligible))
    drawn = board.draw_tokens(eligible[3])  # Take the first eligible draw
    print("Drawn tokens:", drawn)
    print(board)