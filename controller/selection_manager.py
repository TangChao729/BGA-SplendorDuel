from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

class SelectionType(Enum):
    """Types of elements that can be selected."""
    TOKEN = "token"
    PYRAMID_CARD = "pyramid_card"
    RESERVED_CARD = "reserved_card"
    ROYAL_CARD = "royal_card"
    PRIVILEGE = "privilege"
    BAG = "bag"

@dataclass
class SelectedElement:
    """Represents a single selected element."""
    element_type: SelectionType
    position: Tuple[int, ...] # flexible position (row, col) or (level, index) etc.
    metadata: Dict[str, Any]  # element-specific data (color, card, etc.)
    
    def __str__(self) -> str:
        """Human readable representation for debugging."""
        if self.element_type == SelectionType.TOKEN:
            color = self.metadata.get('color', 'unknown')
            return f"Token({color} at {self.position})"
        elif self.element_type == SelectionType.PYRAMID_CARD:
            card = self.metadata.get('card')
            if card:
                # Card object - access id attribute directly
                card_id = getattr(card, 'id', 'unknown') if hasattr(card, 'id') else str(card)
            else:
                # Check if this is a face-down card (index -1)
                if len(self.position) > 1 and self.position[1] == -1:
                    card_id = 'face-down'
                else:
                    card_id = 'unknown'
            return f"PyramidCard({card_id} at level {self.position[0]}, index {self.position[1]})"
        elif self.element_type == SelectionType.RESERVED_CARD:
            card = self.metadata.get('card')
            if card:
                # Card object - access id attribute directly
                card_id = getattr(card, 'id', 'unknown') if hasattr(card, 'id') else str(card)
            else:
                card_id = 'unknown'
            return f"ReservedCard({card_id} at index {self.position[0]})"
        elif self.element_type == SelectionType.ROYAL_CARD:
            card = self.metadata.get('card')
            if card:
                # Card object - access id attribute directly
                card_id = getattr(card, 'id', 'unknown') if hasattr(card, 'id') else str(card)
            else:
                card_id = 'unknown'
            return f"RoyalCard({card_id} at index {self.position[0]})"
        elif self.element_type == SelectionType.PRIVILEGE:
            return f"Privilege(at {self.position})"
        elif self.element_type == SelectionType.BAG:
            return f"Bag(token storage)"
        return f"{self.element_type.value}({self.position})"

class SelectionManager:
    """
    Manages all current user selections in a centralized way.
    Provides validation and state management for multi-step selections.
    """
    
    def __init__(self):
        self.selections: List[SelectedElement] = []
        self.last_selected: Optional[SelectedElement] = None
        
    def add_selection(self, element_type: SelectionType, position: Tuple[int, ...], metadata: Dict[str, Any]) -> bool:
        """
        Add a new selection. Returns True if successfully added.
        
        Args:
            element_type: Type of element being selected
            position: Position coordinates of the element
            metadata: Additional data about the element
            
        Returns:
            bool: True if selection was added, False if already selected
        """
        # Check if already selected
        for selection in self.selections:
            if (selection.element_type == element_type and 
                selection.position == position):
                return False  # Already selected
                
        new_selection = SelectedElement(element_type, position, metadata)
        self.selections.append(new_selection)
        self.last_selected = new_selection
        return True
        
    def remove_selection(self, element_type: SelectionType, position: Tuple[int, ...]) -> bool:
        """
        Remove a selection. Returns True if successfully removed.
        
        Args:
            element_type: Type of element to deselect
            position: Position coordinates of the element
            
        Returns:
            bool: True if selection was removed, False if not found
        """
        for i, selection in enumerate(self.selections):
            if (selection.element_type == element_type and 
                selection.position == position):
                removed = self.selections.pop(i)
                if self.last_selected == removed:
                    self.last_selected = self.selections[-1] if self.selections else None
                return True
        return False
        
    def toggle_selection(self, element_type: SelectionType, position: Tuple[int, ...], metadata: Dict[str, Any]) -> bool:
        """
        Toggle a selection (add if not selected, remove if selected).
        
        Returns:
            bool: True if now selected, False if now deselected
        """
        if not self.remove_selection(element_type, position):
            self.add_selection(element_type, position, metadata)
            return True
        return False
        
    def is_selected(self, element_type: SelectionType, position: Tuple[int, ...]) -> bool:
        """Check if an element is currently selected."""
        for selection in self.selections:
            if (selection.element_type == element_type and 
                selection.position == position):
                return True
        return False
        
    def get_selections_by_type(self, element_type: SelectionType) -> List[SelectedElement]:
        """Get all selections of a specific type."""
        return [s for s in self.selections if s.element_type == element_type]
        
    def get_token_selections(self) -> List[SelectedElement]:
        """Get all selected tokens."""
        return self.get_selections_by_type(SelectionType.TOKEN)
        
    def get_card_selections(self) -> List[SelectedElement]:
        """Get all selected cards (pyramid + reserved)."""
        pyramid_cards = self.get_selections_by_type(SelectionType.PYRAMID_CARD)
        reserved_cards = self.get_selections_by_type(SelectionType.RESERVED_CARD)
        return pyramid_cards + reserved_cards
        
    def clear_all(self) -> None:
        """Clear all selections."""
        self.selections.clear()
        self.last_selected = None
        
    def clear_by_type(self, element_type: SelectionType) -> None:
        """Clear all selections of a specific type."""
        self.selections = [s for s in self.selections if s.element_type != element_type]
        if self.last_selected and self.last_selected.element_type == element_type:
            self.last_selected = self.selections[-1] if self.selections else None
            
    def get_selection_count(self) -> int:
        """Get total number of selections."""
        return len(self.selections)
        
    def get_selection_count_by_type(self, element_type: SelectionType) -> int:
        """Get number of selections of a specific type."""
        return len(self.get_selections_by_type(element_type))
        
    def get_debug_summary(self) -> str:
        """Get a debug summary of current selections."""
        if not self.selections:
            return "No selections"
            
        summary_parts = []
        by_type = {}
        for selection in self.selections:
            type_name = selection.element_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(selection)
            
        for type_name, elements in by_type.items():
            summary_parts.append(f"{type_name}: {len(elements)}")
            
        return f"Selected: {', '.join(summary_parts)} (Total: {len(self.selections)})"
        
    def get_last_selected_summary(self) -> str:
        """Get a summary of the last selected element."""
        if not self.last_selected:
            return "None"
        return str(self.last_selected)
        
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"SelectionManager({len(self.selections)} selections)"
        
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"SelectionManager(selections={[str(s) for s in self.selections]})" 