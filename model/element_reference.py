from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ElementReference:
    """
    A reference to a selectable game element, decoupled from screen coordinates.

    Replaces LayoutElement for the web backend. Carries the live model object and
    enough metadata for GameStateManager validation, without any Pygame dependencies.

    Attributes:
        name:         Stable string identifier, e.g. "token_board_2_3", "card_L2_slot1".
                      Built deterministically from coordinates so the client and server
                      agree on the same name for the same element.
        element:      The live model object (Token, Card, Royal, Deck, BonusColor, …).
        element_type: String class name: "Token", "Card", "Royal", "Deck", "BonusColor".
                      Always a plain str — avoids the LayoutElement bug where the field
                      was annotated str but stored the type class.
        metadata:     Extra data used by GameStateManager validation, e.g.:
                        board token:    {"position": (r, c), "source": "board"}
                        pyramid card:   {"level": int, "index": int}
                        reserved card:  {"reserved_index": int, "player": str}
                        player token:   {"player": str, "source": "hand"}
                        royal:          {"index": int}
                        bonus color:    {"color": str}
    """
    name: str
    element: Any
    element_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
