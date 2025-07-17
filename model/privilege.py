from typing import Any, Dict
from model.interactive_element import InteractiveElement

class Privilege(InteractiveElement):
    """
    Represents a single privilege token in Splendor Duel.
    
    Privileges are special tokens that allow players to choose any gem color
    when making purchases. Each privilege is an individual interactive object
    that can be selected and clicked.
    
    Attributes:
        id (int): Unique identifier for this privilege (0, 1, 2, etc.)
        selected (bool): Whether this privilege is currently selected (inherited)
        clickable (bool): Whether this privilege can be clicked (inherited)
    """
    
    def __init__(self, id: int, selected: bool = False, clickable: bool = True):
        super().__init__(selected=selected, clickable=clickable)
        self.id = id
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Privilege to a dictionary."""
        return {
            "id": self.id,
            "selected": self.selected,
            "clickable": self.clickable,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Privilege":
        """Create a Privilege instance from a dictionary."""
        return cls(
            id=data.get("id", 0),
            selected=data.get("selected", False),
            clickable=data.get("clickable", True),
        )
    
    def __repr__(self) -> str:
        selection_indicator = "✓" if self.selected else ""
        return f"<Privilege id={self.id}{selection_indicator}>"
    
    def __eq__(self, other) -> bool:
        """Privileges are equal if they have the same id."""
        if not isinstance(other, Privilege):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on id only (immutable property) so Privilege can be used as dict key."""
        return hash(self.id) 