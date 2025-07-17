from typing import Dict, List, Tuple, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass

from model.actions import GameState
from controller.selection_manager import SelectionType, SelectionManager

class ElementVisualState(Enum):
    """Visual states that elements can have."""
    NORMAL = "normal"           # Default state
    HIGHLIGHTED = "highlighted" # Available for selection
    SELECTED = "selected"       # Currently selected
    DISABLED = "disabled"       # Not available/grayed out
    PULSING = "pulsing"        # Indicating important action
    ERROR = "error"            # Invalid selection

@dataclass
class ElementState:
    """Represents the visual state of a UI element."""
    visual_state: ElementVisualState
    clickable: bool
    tooltip: Optional[str] = None
    
class ElementStateManager:
    """
    Determines the visual state of all interactive elements based on current game state.
    This manager is pure - it only computes states, doesn't modify anything.
    """
    
    def __init__(self):
        pass
        
    def get_element_state(
        self, 
        element_type: str, 
        element_metadata: Dict[str, Any],
        game_state: GameState,
        selection_manager: SelectionManager,
        current_player_state: Any = None
    ) -> ElementState:
        """
        Determine the visual state of a specific element.
        
        Args:
            element_type: Type of element (from layout registry)
            element_metadata: Element metadata (position, color, card, etc.)
            game_state: Current game state
            selection_manager: Current selection state
            current_player_state: Current player's state (for affordability checks)
            
        Returns:
            ElementState: Visual state information for the element
        """
        # For debugging mode, allow most elements to be selectable
        if self._is_debug_mode():
            return self._get_debug_element_state(element_type, element_metadata, selection_manager)
            
        # Normal game mode logic (TODO: implement when we add game logic)
        return self._get_normal_element_state(element_type, element_metadata, game_state, selection_manager, current_player_state)
        
    def _is_debug_mode(self) -> bool:
        """Check if we're in debug mode (for now, always True)."""
        return True  # For Phase 1, we're always in debug mode
        
    def _get_debug_element_state(
        self, 
        element_type: str, 
        element_metadata: Dict[str, Any],
        selection_manager: SelectionManager
    ) -> ElementState:
        """Get element state for debug mode - most things are selectable."""
        
        # Action buttons are never selectable in debug mode
        if element_type == "action_button":
            return ElementState(
                visual_state=ElementVisualState.NORMAL,
                clickable=False,
                tooltip="Action buttons not selectable in debug mode"
            )
            
        # Check if element is currently selected
        selection_type, position = self._get_selection_info(element_type, element_metadata)
        if selection_type and selection_manager.is_selected(selection_type, position):
            return ElementState(
                visual_state=ElementVisualState.HIGHLIGHTED,  # Selected elements show yellow
                clickable=True,
                tooltip=f"Click to deselect {element_type}"
            )
            
        # Everything else is selectable but not highlighted in debug mode
        return ElementState(
            visual_state=ElementVisualState.NORMAL,  # Non-selected elements show no highlighting
            clickable=True,
            tooltip=f"Click to select {element_type}"
        )
        
    def _get_normal_element_state(
        self,
        element_type: str,
        element_metadata: Dict[str, Any], 
        game_state: GameState,
        selection_manager: SelectionManager,
        current_player_state: Any
    ) -> ElementState:
        """Get element state for normal game mode (TODO: implement full logic)."""
        
        # For now, return normal state for everything
        # This will be expanded when we implement full game logic
        return ElementState(
            visual_state=ElementVisualState.NORMAL,
            clickable=False,
            tooltip="Normal game mode logic not implemented yet"
        )
        
    def _get_selection_info(self, element_type: str, element_metadata: Dict[str, Any]) -> Tuple[Optional[SelectionType], Tuple[int, ...]]:
        """Convert element information to selection type and position."""
        
        if element_type == "token":
            row = element_metadata.get("row", -1)
            col = element_metadata.get("col", -1)
            return SelectionType.TOKEN, (row, col)
            
        elif element_type == "pyramid_card":
            level = element_metadata.get("level", -1)
            index = element_metadata.get("index", -1)
            return SelectionType.PYRAMID_CARD, (level, index)
            
        elif element_type == "pyramid_card_back":
            # Face-down pyramid cards - use level and special index -1 to indicate back
            level = element_metadata.get("level", -1)
            return SelectionType.PYRAMID_CARD, (level, -1)
            
        elif element_type == "reserved_card":
            index = element_metadata.get("index", -1)
            return SelectionType.RESERVED_CARD, (index,)
            
        elif element_type == "royal_card":
            index = element_metadata.get("index", -1)
            return SelectionType.ROYAL_CARD, (index,)
            
        elif element_type == "privilege":
            # Privileges might not have position, use 0 as default
            index = element_metadata.get("index", 0)
            return SelectionType.PRIVILEGE, (index,)
            
        elif element_type == "bag":
            # Bag has no specific position, use (0,) as placeholder
            return SelectionType.BAG, (0,)
            
        return None, ()
        
    def get_all_element_states(
        self,
        elements: List[Tuple[str, Dict[str, Any]]],  # (element_type, metadata) pairs
        game_state: GameState,
        selection_manager: SelectionManager,
        current_player_state: Any = None
    ) -> Dict[Tuple[str, str], ElementState]:
        """
        Get visual states for all elements.
        
        Args:
            elements: List of (element_type, metadata) pairs
            game_state: Current game state
            selection_manager: Current selection state
            current_player_state: Current player's state
            
        Returns:
            Dict mapping (element_type, element_id) to ElementState
        """
        states = {}
        
        for element_type, metadata in elements:
            # Create a unique ID for this element
            element_id = self._create_element_id(element_type, metadata)
            
            state = self.get_element_state(
                element_type, 
                metadata, 
                game_state, 
                selection_manager, 
                current_player_state
            )
            
            states[(element_type, element_id)] = state
            
        return states
        
    def _create_element_id(self, element_type: str, metadata: Dict[str, Any]) -> str:
        """Create a unique ID for an element based on its type and metadata."""
        
        if element_type == "token":
            row = metadata.get("row", -1)
            col = metadata.get("col", -1)
            return f"token_{row}_{col}"
            
        elif element_type == "pyramid_card":
            level = metadata.get("level", -1)
            index = metadata.get("index", -1)
            return f"pyramid_card_{level}_{index}"
            
        elif element_type == "reserved_card":
            index = metadata.get("index", -1)
            return f"reserved_card_{index}"
            
        elif element_type == "royal_card":
            index = metadata.get("index", -1)
            return f"royal_card_{index}"
            
        elif element_type == "privilege":
            index = metadata.get("index", 0)
            return f"privilege_{index}"
            
        elif element_type == "action_button":
            action = metadata.get("button", {}).get("action", "unknown")
            return f"action_button_{action}"
            
        # Fallback for unknown element types
        return f"{element_type}_unknown"
        
    def get_debug_info(self, selection_manager: SelectionManager) -> Dict[str, Any]:
        """Get debug information about current element states."""
        return {
            "debug_mode": self._is_debug_mode(),
            "total_selections": selection_manager.get_selection_count(),
            "selections_by_type": {
                "tokens": selection_manager.get_selection_count_by_type(SelectionType.TOKEN),
                "pyramid_cards": selection_manager.get_selection_count_by_type(SelectionType.PYRAMID_CARD),
                "reserved_cards": selection_manager.get_selection_count_by_type(SelectionType.RESERVED_CARD),
                "royal_cards": selection_manager.get_selection_count_by_type(SelectionType.ROYAL_CARD),
                "privileges": selection_manager.get_selection_count_by_type(SelectionType.PRIVILEGE),
                "bag": selection_manager.get_selection_count_by_type(SelectionType.BAG),
            }
        } 