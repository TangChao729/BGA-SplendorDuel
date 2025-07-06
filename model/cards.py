import json
import random
from typing import Any, Dict, List, Optional
from model.tokens import Token

random.seed(42)  # For reproducibility in tests


class Card:
    """
    Represents a single Jewel card in Splendor Duel.

    Attributes:
        id (str): Unique identifier (e.g. "1-01", "2-05").
        level (int): Card level (1, 2, or 3).
        color (str): Gem color or special type ("Black", "Red", "Green", "Blue", "White").
        points (int): Prestige points awarded when purchased.
        bonus (int): Permanent gem bonus provided.
        ability (Optional[str]): One of the special abilities ("Turn", "steal", etc.) or None.
        crowns (int): Number of crowns on the card.
        cost (Dict[Token, int]): Token cost mapping (e.g. {"black": 1, "red": 2, ...}).
    """

    def __init__(
        self,
        id: str,
        level: int,
        color: str,
        points: int,
        bonus: int,
        ability: Optional[str],
        crowns: int,
        cost: Dict[Token, int],
    ):
        self.id = id
        self.level = level
        self.color = color
        self.points = points
        self.bonus = bonus
        self.ability = ability
        self.crowns = crowns
        self.cost = cost

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Card":
        """
        Create a Card instance from a dictionary.
        """
        return cls(
            id=data.get("id"),
            level=int(data.get("level", 0)),
            color=data.get("color"),
            points=int(data.get("points", 0)),
            bonus=int(data.get("bonus", 0)),
            ability=data.get("ability"),
            crowns=int(data.get("crowns", 0)),
            cost={t: int(v) for t, v in data.get("cost", {}).items()},
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the Card to a dictionary.
        """
        return {
            "id": self.id,
            "level": self.level,
            "color": self.color,
            "points": self.points,
            "bonus": self.bonus,
            "ability": self.ability,
            "crowns": self.crowns,
            "cost": dict(self.cost),
        }

    def __repr__(self) -> str:
        return (
            f"<Card id={self.id!r} level={self.level} color={self.color!r} "
            f"points={self.points} bonus={self.bonus} crowns={self.crowns}>"
        )


class Deck:
    """
    Manages a shuffled deck of Card instances.

    Responsibilities:
        - Initialize from a list of Card objects.
        - Shuffle and draw cards.
        - Track remaining cards.
    """

    def __init__(self, cards: List[Card]):
        self._cards: List[Card] = cards.copy()
        self.shuffle()

    def shuffle(self) -> None:
        """
        Shuffle the deck in-place.
        """
        random.shuffle(self._cards)

    def draw(self, num: int = 1) -> List[Card]:
        """
        Draw and remove `num` cards from the top of the deck.
        """
        drawn = self._cards[:num]
        self._cards = self._cards[num:]
        return drawn

    def peek(self, num: int = 1) -> List[Card]:
        """
        Return the next `num` cards without removing them.
        """
        return self._cards[:num]

    def add_cards(self, cards: List[Card]) -> None:
        """
        Add a list of cards to the bottom of the deck.
        """
        self._cards.extend(cards)

    def __len__(self) -> int:
        """
        Return the number of cards remaining in the deck.
        """
        return len(self._cards)

    @classmethod
    def from_json(
        cls, json_path: str, level: Optional[int] = None
    ) -> "Deck":
        """
        Build a Deck by loading card data from a JSON file.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cards: List[Card] = []
        if level is not None:
            key = f"level_{level}"
            for entry in data.get(key, []):
                cards.append(Card.from_dict(entry))
        else:
            for entries in data.values():
                for entry in entries:
                    cards.append(Card.from_dict(entry))
        return cls(cards)


class Royal:
    """
    Represents a Royal card in Splendor Duel.

    Attributes:
        id (str): Unique identifier.
        points (int): Prestige points when claimed.
        ability (Optional[str]): Special ability or None.
    """

    def __init__(self, id: str, points: int, ability: Optional[str]):
        self.id = id
        self.points = points
        self.ability = ability

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Royal":
        return cls(
            id=data.get("id"),
            points=int(data.get("points", 0)),
            ability=data.get("ability"),
        )

    @classmethod
    def from_json(cls, json_path: str) -> List["Royal"]:
        """
        Load Royal cards from a JSON file.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [cls.from_dict(entry) for entry in data.get("royals", [])]

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "points": self.points, "ability": self.ability}

    def __repr__(self) -> str:
        return f"<Royal id={self.id!r} points={self.points} ability={self.ability!r}>"


class Pyramid:
    """
    Manages the pyramid layout of cards in Splendor Duel.

    Attributes:
        decks (Dict[int, Deck]): Deck instances keyed by level.
        slots (Dict[int, List[Optional[Card]]]): Face-up cards per level, with variable slot counts.
    """

    # Define number of face-up slots per level: level 3=3 slots, level 2=4 slots, level 1=5 slots
    SLOT_COUNTS: Dict[int, int] = {3: 3, 2: 4, 1: 5}

    def __init__(self, decks: Dict[int, Deck]):
        self.decks = decks
        self.slots: Dict[int, List[Optional[Card]]] = {}
        for level, deck in decks.items():
            count = self.SLOT_COUNTS.get(level, 3)
            self.slots[level] = deck.draw(count)

    def get_card(self, level: int, index: int) -> Optional[Card]:        
        drawn = self.slots[level][index]
        if drawn:
            self.slots[level][index] = None  # Remove card after getting it
            return drawn  # Return the drawn card or None if empty
        return None

    def fill_card(self, level: int, index: int) -> None:
        drawn = self.decks[level].draw(1)
        self.slots[level][index] = drawn[0] if drawn else None

    def to_dict(self) -> Dict[int, List[Optional[Dict[str, Any]]]]:
        return {
            level: [c.to_dict() if c else None for c in cards]
            for level, cards in self.slots.items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[int, List[Optional[Dict[str, Any]]]]) -> "Pyramid":
        """
        Load Pyramid slots from a dictionary.
        """
        # Create empty decks for each level (since we're reconstructing from slots)
        decks = {level: Deck([]) for level in data.keys()}
        pyramid = cls(decks)
        
        # Override the slots with the provided data
        pyramid.slots = {}
        for level, cards in data.items():
            pyramid.slots[int(level)] = [
                Card.from_dict(card) if card else None for card in cards
            ]
        return pyramid

    def __repr__(self) -> str:
        parts: List[str] = []
        for level, cards in self.slots.items():
            ids = ",".join(c.id if c else "None" for c in cards)
            parts.append(f"L{level}:[{ids}]")
        return f"Pyramid\n{'\n'.join(parts)}"
