from typing import Any, Dict
from model.interactive_element import InteractiveElement
from model.tokens import Bag

class InteractiveBag(InteractiveElement):
    """
    Interactive wrapper around the Bag class that allows the bag to be selected and clicked.
    
    The bag represents the token storage that players can interact with during certain
    game actions (like drawing gold tokens and reserving cards).
    
    Attributes:
        bag (Bag): The underlying token bag containing all tokens
        selected (bool): Whether this bag is currently selected (inherited)
        clickable (bool): Whether this bag can be clicked (inherited)
    """
    
    def __init__(self, bag: Bag, selected: bool = False, clickable: bool = True):
        super().__init__(selected=selected, clickable=clickable)
        self.bag = bag
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the InteractiveBag to a dictionary."""
        return {
            "bag_counts": self.bag.counts(),
            "selected": self.selected,
            "clickable": self.clickable,
        }
    
    @classmethod
    def from_bag(cls, bag: Bag, selected: bool = False, clickable: bool = True) -> "InteractiveBag":
        """Create an InteractiveBag from an existing Bag instance."""
        return cls(bag=bag, selected=selected, clickable=clickable)
    
    @classmethod
    def from_json(cls, file_path: str, selected: bool = False, clickable: bool = True) -> "InteractiveBag":
        """Create an InteractiveBag from a JSON file."""
        bag = Bag.from_json(file_path)
        return cls(bag=bag, selected=selected, clickable=clickable)
    
    def __repr__(self) -> str:
        selection_indicator = "✓" if self.selected else ""
        counts = self.bag.counts()
        total_tokens = sum(counts.values())
        return f"<InteractiveBag tokens={total_tokens}{selection_indicator}>"
    
    def __eq__(self, other) -> bool:
        """Bags are equal if they have the same token counts."""
        if not isinstance(other, InteractiveBag):
            return False
        return self.bag.counts() == other.bag.counts()
    
    def __hash__(self) -> int:
        """Hash based on sorted token counts (for dict key usage)."""
        counts = self.bag.counts()
        sorted_items = tuple(sorted(counts.items()))
        return hash(sorted_items)
    
    # Delegate bag methods for convenience
    def counts(self) -> Dict[str, int]:
        """Return the current count of tokens by color."""
        return self.bag.counts()
    
    def draw(self):
        """Shuffle and return all tokens, emptying the bag."""
        return self.bag.draw()
    
    def return_tokens(self, tokens):
        """Return a list of tokens to the bag."""
        return self.bag.return_tokens(tokens) 