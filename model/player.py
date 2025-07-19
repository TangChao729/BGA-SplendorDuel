import json
from typing import Dict, List, Optional, Any

from model.cards import Card
from model.tokens import Token


class PlayerState:
    """
    Holds the state for one player in Splendor Duel.

    Attributes:
        tokens (Dict[token,int]): Player's available tokens by color (including wild 'pearl').
        bonuses (Dict[token,int]): Permanent gem bonuses from purchased cards by color.
        reserved (List[Card]): Up to 3 reserved cards.
        purchased (List[Card]): Cards the player has purchased.
        privileges (int): Number of privilege scrolls the player holds.
        crowns (int): Total crowns from purchased cards.
        points (int): Total prestige points scored.
    """

    def __init__(self, name: str = "default") -> None:
        self.name: Optional[str] = name
        # token colors: black, red, green, blue, white, pearl, gold (wild)
        self.tokens: Dict[Token, int] = {
            Token(c): 0 for c in ["black", "red", "green", "blue", "white", "pearl", "gold"]
        }
        # bonuses from purchased cards (no wild bonus)
        self.bonuses: Dict[Token, int] = {
            Token(c): 0 for c in ["black", "red", "green", "blue", "white"]
        }
        self.reserved: List[Card] = []
        self.purchased: List[Card] = []
        self.privileges: int = 0
        self.crowns: int = 0
        self.points: int = 0
        # points from cards of same color
        self.card_points: Dict[str, int] = {
            c: 0 for c in ["black", "red", "green", "blue", "white"]
        }

    # add token by color str
    def add_tokens(self, list_tokens: List[Token]) -> None:
        """
        Add tokens of given colors to player's supply.
        """
        for token in list_tokens:
            self.tokens[token] = self.tokens.get(token, 0) + 1
            
    def remove_tokens(self, spend: Dict[Token, int]) -> None:
        """
        Remove specified token counts from player's supply.

        Args:
            spend (Dict[str,int]): Map color to number of tokens to deduct.
        """
        for token, amt in spend.items():
            if amt > 0:
                assert self.tokens[token] >= amt, f"Not enough tokens of color {token}"
                self.tokens[token] -= amt

    def can_afford(self, card: Card) -> bool:
        """
        Check whether the player can afford the card, considering tokens, bonuses, and wild tokens.

        Returns:
            bool: True if affordable, False otherwise.
        """
        cost: Dict[Token, int] = card.cost
        # compute shortage per color after bonuses and personal tokens
        total_short = 0
        for token, required in cost.items():
            bonus = self.bonuses.get(token, 0)
            have = self.tokens.get(token, 0) + bonus
            short = max(required - have, 0)
            total_short += short
        # wild tokens (pearl) can cover shortage
        return total_short <= self.tokens.get(Token("gold"), 0)

    def pay_for_card(self, card: Card) -> None:
        """
        Deduct tokens to pay for the card, apply its bonuses, crowns, and points.
        Assumes can_afford(card) is True.
        """
        cost = card.cost
        to_remove: Dict[Token, int] = {token: 0 for token in self.tokens}
        # First use colored tokens up to cost - bonus
        for token, required in cost.items():
            bonus = self.bonuses.get(token, 0)
            needed = max(required - bonus, 0)
            pay_color = min(self.tokens.get(token, 0), needed)
            to_remove[token] = pay_color
        # Compute leftover shortage to cover with wild
        shortage = sum(
            max(card.cost[c] - (self.bonuses.get(c, 0) + to_remove.get(c, 0)), 0)
            for c in cost
        )
        to_remove[Token("gold")] = shortage
        # Remove tokens
        self.remove_tokens(to_remove)
        # Acquire card
        self.purchased.append(card)
        # Update bonuses, points, crowns
        self.bonuses[Token(card.color)] = self.bonuses.get(Token(card.color), 0) + 1
        self.points += card.points
        self.crowns += card.crowns

    def reserve_card(self, card: Card) -> bool:
        """
        Reserve a card into player's hand (up to 3). Returns True if successful.
        """
        if len(self.reserved) < 3:
            self.reserved.append(card)
            return True
        return False

    def use_privilege(self) -> bool:
        """
        Spend one privilege scroll if available.

        Returns:
            bool: True if spent, False otherwise.
        """
        if self.privileges > 0:
            self.privileges -= 1
            return True
        return False

    def add_privilege(self, count: int = 1) -> None:
        """
        Add privilege scrolls to player.
        """
        self.privileges += count

    def __repr__(self) -> str:
        return (
            f"<PlayerState tokens={self.tokens} bonuses={self.bonuses} "
            f"reserved={len(self.reserved)} purchased={len(self.purchased)} "
            f"points={self.points} crowns={self.crowns} privileges={self.privileges}>"
        )

    def has_won(self) -> bool:
        """
        Check victory conditions: total prestige >=20, crowns >=10,
        or prestige points on cards of same color >=10.
        """
        # Total prestige points
        if self.points >= 20:
            return True
        # Total crowns
        if self.crowns >= 10:
            return True
        # Prestige points grouped by card color
        color_scores: Dict[str, int] = {}
        for card in self.purchased:
            color_scores[card.color] = color_scores.get(card.color, 0) + card.points
        if any(score >= 10 for score in color_scores.values()):
            return True
        return False
    
    def get_token_count(self) -> int:
        """
        Get the total number of tokens the player has
        """
        return sum(self.tokens.values())

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize the player state to a JSON-compatible dictionary.
        
        Returns:
            Dict[str, Any]: JSON-serializable representation of the player state.
        """
        return {
            "name": self.name,
            "tokens": {token.color: count for token, count in self.tokens.items()},
            "bonuses": {token.color: count for token, count in self.bonuses.items()},
            "reserved": [card.to_dict() for card in self.reserved],
            "purchased": [card.to_dict() for card in self.purchased],
            "privileges": self.privileges,
            "crowns": self.crowns,
            "points": self.points,
            "card_points": self.card_points.copy()
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "PlayerState":
        """
        Create a PlayerState instance from a JSON-compatible dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing player state data.
            
        Returns:
            PlayerState: Reconstructed player state.
        """
        player = cls()
        
        # Set basic attributes
        player.name = data.get("name", "Player")
        player.tokens = {Token(c): data.get("tokens", {c: 0 for c in ["black", "red", "green", "blue", "white", "pearl", "gold"]})[c] for c in ["black", "red", "green", "blue", "white", "pearl", "gold"]}
        player.bonuses = {Token(c): data.get("bonuses", {c: 0 for c in ["black", "red", "green", "blue", "white"]})[c] for c in ["black", "red", "green", "blue", "white"]}
        player.privileges = data.get("privileges", 0)
        player.crowns = data.get("crowns", 0)
        player.points = data.get("points", 0)
        player.card_points = data.get("card_points", {c: 0 for c in ["black", "red", "green", "blue", "white"]})
        
        # Reconstruct card lists
        player.reserved = [Card.from_dict(card_data) for card_data in data.get("reserved", [])]
        player.purchased = [Card.from_dict(card_data) for card_data in data.get("purchased", [])]
        
        return player

    def save_to_file(self, filename: str) -> None:
        """
        Save the player state to a JSON file.
        
        Args:
            filename (str): Path to the output JSON file.
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_json(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filename: str) -> "PlayerState":
        """
        Load a player state from a JSON file.
        
        Args:
            filename (str): Path to the JSON file.
            
        Returns:
            PlayerState: Loaded player state.
        """
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_json(data)
