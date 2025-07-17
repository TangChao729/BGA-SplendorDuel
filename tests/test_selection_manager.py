import pytest
from controller.selection_manager import SelectionManager, SelectionType, SelectedElement

class TestSelectionManager:
    
    def test_initial_state(self):
        """Test that SelectionManager starts in empty state."""
        manager = SelectionManager()
        assert manager.get_selection_count() == 0
        assert manager.last_selected is None
        assert manager.get_debug_summary() == "No selections"
    
    def test_add_selection(self):
        """Test adding a selection."""
        manager = SelectionManager()
        
        # Add a token selection
        result = manager.add_selection(
            SelectionType.TOKEN, 
            (0, 1), 
            {"color": "red", "token": None}
        )
        
        assert result is True
        assert manager.get_selection_count() == 1
        assert manager.is_selected(SelectionType.TOKEN, (0, 1))
        assert manager.last_selected.element_type == SelectionType.TOKEN
        assert manager.last_selected.position == (0, 1)
    
    def test_add_duplicate_selection(self):
        """Test that adding the same selection twice doesn't create duplicates."""
        manager = SelectionManager()
        
        # Add selection twice
        result1 = manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        result2 = manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        
        assert result1 is True
        assert result2 is False  # Should not add duplicate
        assert manager.get_selection_count() == 1
    
    def test_remove_selection(self):
        """Test removing a selection."""
        manager = SelectionManager()
        
        # Add then remove
        manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        result = manager.remove_selection(SelectionType.TOKEN, (0, 1))
        
        assert result is True
        assert manager.get_selection_count() == 0
        assert not manager.is_selected(SelectionType.TOKEN, (0, 1))
        assert manager.last_selected is None
    
    def test_remove_nonexistent_selection(self):
        """Test removing a selection that doesn't exist."""
        manager = SelectionManager()
        
        result = manager.remove_selection(SelectionType.TOKEN, (0, 1))
        
        assert result is False
        assert manager.get_selection_count() == 0
    
    def test_toggle_selection(self):
        """Test toggling selections."""
        manager = SelectionManager()
        
        # Toggle on
        result1 = manager.toggle_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        assert result1 is True
        assert manager.is_selected(SelectionType.TOKEN, (0, 1))
        
        # Toggle off
        result2 = manager.toggle_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        assert result2 is False
        assert not manager.is_selected(SelectionType.TOKEN, (0, 1))
    
    def test_get_selections_by_type(self):
        """Test filtering selections by type."""
        manager = SelectionManager()
        
        # Add different types
        manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        manager.add_selection(SelectionType.TOKEN, (1, 1), {"color": "blue"})
        manager.add_selection(SelectionType.PYRAMID_CARD, (1, 0), {"card": None})
        
        tokens = manager.get_token_selections()
        cards = manager.get_card_selections()
        
        assert len(tokens) == 2
        assert len(cards) == 1
        assert manager.get_selection_count_by_type(SelectionType.TOKEN) == 2
        assert manager.get_selection_count_by_type(SelectionType.PYRAMID_CARD) == 1
    
    def test_clear_all(self):
        """Test clearing all selections."""
        manager = SelectionManager()
        
        # Add multiple selections
        manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        manager.add_selection(SelectionType.PYRAMID_CARD, (1, 0), {"card": None})
        
        manager.clear_all()
        
        assert manager.get_selection_count() == 0
        assert manager.last_selected is None
    
    def test_clear_by_type(self):
        """Test clearing selections by type."""
        manager = SelectionManager()
        
        # Add different types
        manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        manager.add_selection(SelectionType.TOKEN, (1, 1), {"color": "blue"})
        manager.add_selection(SelectionType.PYRAMID_CARD, (1, 0), {"card": None})
        
        manager.clear_by_type(SelectionType.TOKEN)
        
        assert manager.get_selection_count() == 1
        assert manager.get_selection_count_by_type(SelectionType.TOKEN) == 0
        assert manager.get_selection_count_by_type(SelectionType.PYRAMID_CARD) == 1
    
    def test_selected_element_string_representation(self):
        """Test string representations of SelectedElement."""
        
        # Test token
        token_element = SelectedElement(
            SelectionType.TOKEN, 
            (0, 1), 
            {"color": "red"}
        )
        assert "Token(red at (0, 1))" in str(token_element)
        
        # Mock card object for testing
        class MockCard:
            def __init__(self, card_id):
                self.id = card_id
        
        # Test pyramid card with actual card object
        card_element = SelectedElement(
            SelectionType.PYRAMID_CARD,
            (2, 1),
            {"card": MockCard("test-card")}
        )
        assert "PyramidCard(test-card at level 2, index 1)" in str(card_element)
        
        # Test reserved card with actual card object
        reserved_element = SelectedElement(
            SelectionType.RESERVED_CARD,
            (0,),
            {"card": MockCard("reserved-card")}
        )
        assert "ReservedCard(reserved-card at index 0)" in str(reserved_element)
        
        # Test bag
        bag_element = SelectedElement(
            SelectionType.BAG,
            (0,),
            {"desk": None}
        )
        assert "Bag(token storage)" in str(bag_element)
        
        # Test face-down pyramid card
        facedown_element = SelectedElement(
            SelectionType.PYRAMID_CARD,
            (2, -1),
            {"level": 2, "deck_type": "face_down"}
        )
        assert "PyramidCard(face-down at level 2, index -1)" in str(facedown_element)
    
    def test_debug_summary(self):
        """Test debug summary functionality."""
        manager = SelectionManager()
        
        # Mock card for testing
        class MockCard:
            def __init__(self, card_id):
                self.id = card_id
        
        # Add various selections
        manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        manager.add_selection(SelectionType.TOKEN, (1, 1), {"color": "blue"})
        manager.add_selection(SelectionType.PYRAMID_CARD, (1, 0), {"card": MockCard("test")})
        
        summary = manager.get_debug_summary()
        assert "token: 2" in summary
        assert "pyramid_card: 1" in summary
        assert "Total: 3" in summary
        
        last_summary = manager.get_last_selected_summary()
        assert "test" in last_summary  # Should show the last selected card
    
    def test_last_selected_tracking(self):
        """Test that last_selected is properly tracked."""
        manager = SelectionManager()
        
        # Mock card for testing
        class MockCard:
            def __init__(self, card_id):
                self.id = card_id
        
        # Add selections
        manager.add_selection(SelectionType.TOKEN, (0, 1), {"color": "red"})
        token_selection = manager.last_selected
        
        manager.add_selection(SelectionType.PYRAMID_CARD, (1, 0), {"card": MockCard("test")})
        card_selection = manager.last_selected
        
        assert card_selection != token_selection
        assert card_selection.element_type == SelectionType.PYRAMID_CARD
        
        # Remove the last selected
        manager.remove_selection(SelectionType.PYRAMID_CARD, (1, 0))
        assert manager.last_selected == token_selection  # Should fall back to previous 