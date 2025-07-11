from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


class ActionType(Enum):
    """
    Enumeration of all valid action categories in Splendor Duel.

    Members:
        TAKE_TOKENS            - Take up to 3 non-gold tokens.
        TAKE_GOLD_AND_RESERVE  - Take 1 gold token and reserve a card.
        PURCHASE_CARD          - Purchase a card from the board or reserved.
        USE_PRIVILEGE          - Spend a privilege scroll to gain a token.
        REPLENISH_BOARD        - Refill board tokens or cards when required.
    """
    TAKE_TOKENS = "TAKE_TOKENS"
    TAKE_GOLD_AND_RESERVE = "TAKE_GOLD_AND_RESERVE"
    PURCHASE_CARD = "PURCHASE_CARD"
    USE_PRIVILEGE = "USE_PRIVILEGE"
    REPLENISH_BOARD = "REPLENISH_BOARD"


class GameState(Enum):
    """Enumeration of all possible game states."""
    START_OF_ROUND = "start_of_round"
    USE_PRIVILEGE = "use_privilege"
    REPLENISH_BOARD = "replenish_board"
    CHOOSE_MANDATORY_ACTION = "choose_mandatory_action"
    PURCHASE_CARD = "purchase_card"
    TAKE_TOKENS = "take_tokens"
    TAKE_GOLD_AND_RESERVE = "take_gold_and_reserve"
    POST_ACTION_CHECKS = "post_action_checks"
    CONFIRM_ROUND = "confirm_round"


class Action:
    """
    A concrete action instance to be taken by an agent.

    Attributes:
        type (ActionType): Category of action.
        payload (Dict[str, Any]): Additional parameters, e.g.:
            - tokens: List[str] for TAKE_TOKENS
            - level: int and index: int for PURCHASE_CARD or RESERVE
            - card: Card instance when reserving/purchasing reserved
            - colors: List[str] for USE_PRIVILEGE token choices
    """

    def __init__(
        self,
        action_type: ActionType,
        payload: Optional[Dict[str, Any]] = None,
    ):
        self.type: ActionType = action_type
        self.payload: Dict[str, Any] = payload or {}

    def __repr__(self) -> str:
        return f"<Action type={self.type.name} payload={self.payload}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize action for logging or network transmission.

        Returns:
            Dict[str, Any]: JSON-serializable dict of action.
        """
        return {"type": self.type.value, "payload": self.payload}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        """
        Deserialize an Action from a dict.

        Args:
            data (Dict[str, Any]): Dict with keys 'type' and 'payload'.
        Returns:
            Action: Reconstructed Action object.
        """
        action_type = ActionType(data.get("type"))
        payload = data.get("payload", {})
        return cls(action_type, payload)


@dataclass
class ActionButton:
    """Represents a clickable action button."""
    text: str
    action: str
    enabled: bool = True


@dataclass
class CurrentAction:
    """Represents the current game state and available actions."""
    state: GameState
    explanation: str
    buttons: List[ActionButton]
    
    def __post_init__(self):
        if not isinstance(self.state, GameState):
            self.state = GameState(self.state)
