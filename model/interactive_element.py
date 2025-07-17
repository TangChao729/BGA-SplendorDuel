from typing import Optional
from enum import Enum
from dataclasses import dataclass

class VisualState(Enum):
    """Visual states that interactive elements can have."""
    NORMAL = "normal"           # Default state - no highlighting
    HIGHLIGHTED = "highlighted" # Selected state - yellow highlighting
    DISABLED = "disabled"       # Not available/grayed out

@dataclass
class InteractiveElement:
    """
    Base class for all interactive game elements (tokens, cards, privileges, bag, etc.).
    Manages selection state and visual feedback directly within the object.
    """
    selected: bool = False
    clickable: bool = True
    
    @property
    def visual_state(self) -> VisualState:
        """Determine visual state based on current selection and clickability."""
        if not self.clickable:
            return VisualState.DISABLED
        elif self.selected:
            return VisualState.HIGHLIGHTED  # Yellow highlighting when selected
        else:
            return VisualState.NORMAL       # No highlighting when not selected
    
    def toggle_selection(self) -> bool:
        """
        Toggle the selection state of this element.
        
        Returns:
            bool: True if element is now selected, False if deselected
        """
        if not self.clickable:
            return False
            
        self.selected = not self.selected
        return self.selected
    
    def select(self) -> bool:
        """
        Explicitly select this element.
        
        Returns:
            bool: True if selection succeeded, False if not clickable
        """
        if not self.clickable:
            return False
            
        self.selected = True
        return True
    
    def deselect(self) -> None:
        """Explicitly deselect this element."""
        self.selected = False
    
    def set_clickable(self, clickable: bool) -> None:
        """Set whether this element can be clicked."""
        self.clickable = clickable
        if not clickable:
            self.selected = False  # Deselect if made unclickable 