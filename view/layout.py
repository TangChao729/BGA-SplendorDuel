from typing import List, Tuple, Dict

# A simple rectangle type: (x, y, width, height)
Rect = Tuple[int, int, int, int]

class HSplit:
    """
    Horizontally split a rectangle into named sub-rectangles based on weights.
    Example:
        splits = HSplit((0,0,1000,600), [("left",1),("main",2),("right",1)])
        rects = splits.children  # {'left':(0,0,250,600), 'main':(250,0,500,600), 'right':(750,0,250,600)}
    """
    def __init__(self, rect: Rect, splits: List[Tuple[str, float]]):
        self.rect = rect
        self.splits = splits
        self.children: Dict[str, Rect] = self._compute_rects()

    def _compute_rects(self) -> Dict[str, Rect]:
        x, y, w, h = self.rect
        total = sum(weight for _, weight in self.splits)
        rects: Dict[str, Rect] = {}
        offset = x
        for name, weight in self.splits:
            width = int(w * (weight / total))
            rects[name] = (offset, y, width, h)
            offset += width
        return rects

class VSplit:
    """
    Vertically split a rectangle into named sub-rectangles based on weights.
    Example:
        splits = VSplit((0,0,800,600), [("top",1),("bottom",2)])
        rects = splits.children  # {'top':(0,0,800,200), 'bottom':(0,200,800,400)}
    """
    def __init__(self, rect: Rect, splits: List[Tuple[str, float]]):
        self.rect = rect
        self.splits = splits
        self.children: Dict[str, Rect] = self._compute_rects()

    def _compute_rects(self) -> Dict[str, Rect]:
        x, y, w, h = self.rect
        total = sum(weight for _, weight in self.splits)
        rects: Dict[str, Rect] = {}
        offset = y
        for name, weight in self.splits:
            height = int(h * (weight / total))
            rects[name] = (x, offset, w, height)
            offset += height
        return rects

class Margin:
    """
    Inset a rectangle by (left, top, right, bottom) margins.
    Example:
        inner = Margin((0,0,400,300), (10,10,10,10)).rect  # (10,10,380,280)
    """
    def __init__(self, rect: Rect, margins: Tuple[int, int, int, int]):
        x, y, w, h = rect
        left, top, right, bottom = margins
        self.rect: Rect = (
            x + left,
            y + top,
            w - left - right,
            h - top - bottom
        )
