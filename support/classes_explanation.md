# splendor_duel/env.py

class Card:
    """
    Represents a single Jewel card in Splendor Duel.

    Attributes:
        id (str): Unique identifier (e.g. "1-01", "2-05").
        level (int): Card level (1, 2 or 3).
        color (str): Gem color or special type ("Black", "Red", "Green", "Blue", "White", "Points", "Joker").
        points (int): Prestige points awarded when purchased.
        bonus (int): Permanent gem bonus provided.
        ability (Optional[str]): One of the special abilities ("Turn", "steal", "privilege", etc.) or None.
        crowns (int): Number of crowns on the card.
        cost (Dict[str, int]): Token cost (keys: "pearl", "black", "red", "green", "blue", "white").
    """

class Deck:
    """
    Manages a shuffled deck of Cards at a given level.

    Responsibilities:
        - Initialize from a list of Card instances.
        - Shuffle and draw cards.
        - Track remaining cards.
    """

class Token:
    """
    Represents a single token unit.

    Attributes:
        color (str): One of the six token types ("black","red","green","blue","white","pearl") or "gold".
    """

class Bag:
    """
    The bag of tokens used to refill the board.

    Responsibilities:
        - Hold Token instances.
        - Draw all tokens to refill the board.
        - Return spent tokens back into the bag.
    """

class Board:
    """
    Represents the shared game board state.

    Attributes:
        pyramid (List[List[Optional[Card]]]): 3-row pyramid of face-up cards.
        tokens (Dict[str, int]): Count of tokens currently on each board space color.
        privileges (int): Number of privilege scrolls available above the board.
        royal_cards (List[Card]): Face-up royal cards below the board.

    Responsibilities:
        - Initialize layout (shuffle decks, reveal pyramid).
        - Let players take tokens or privileges.
        - Replenish tokens from the Bag.
        - Replace purchased/reserved cards in the pyramid.
    """

class PlayerState:
    """
    Holds the state for one player.

    Attributes:
        tokens (Dict[str, int]): Player’s tokens (including gold).
        bonuses (Dict[str, int]): Permanent bonuses from purchased cards.
        reserved (List[Card]): Up to 3 reserved cards.
        purchased (List[Card]): Cards the player has purchased.
        privileges (int): Number of privilege scrolls the player holds.
        crowns (int): Cumulative crowns from purchased cards.
        points (int): Cumulative prestige points.

    Responsibilities:
        - Apply bonuses when purchasing.
        - Track and resolve card abilities upon purchase.
        - Check victory conditions at end of turn.
    """

from enum import Enum
class ActionType(Enum):
    """
    Enumeration of all valid action categories in Splendor Duel.

    Members:
        TAKE_TOKENS        # up to 3 adjacent non-gold tokens
        TAKE_GOLD_AND_RESERVE  # take 1 gold + reserve a card
        PURCHASE_CARD      # buy from pyramid or reserve
        USE_PRIVILEGE      # spend privilege for tokens
        REPLENISH_BOARD    # refill board from bag (optional/mandatory fallback)
    """

class Action:
    """
    A concrete action instance to be taken by an agent.

    Attributes:
        type (ActionType): Which category of action.
        payload (Dict): Additional parameters, e.g.
            - tokens: List[str] for TAKE_TOKENS
            - card_id: str for PURCHASE_CARD or TAKE_GOLD_AND_RESERVE
            - privilege_returned: int for USE_PRIVILEGE
    """

from gymnasium import spaces, Env
class SplendorDuelEnv(Env):
    """
    Gymnasium-style environment for Splendor Duel.

    Observation:
        A structured dict encoding:
            - Board state (available cards & tokens & privileges & royal cards)
            - PlayerState for each player
            - Current player index

    Action Space:
        A gym.spaces.Discrete or gym.spaces.Dict of all valid Action encodings.

    Reward:
        +1 for winning on your turn, -1 for losing, 0 otherwise.

    Responsibilities:
        - step(action): apply action, advance game state, compute reward, done flag.
        - reset(): reinitialize a new game.
        - render(mode="text"): return a text summary of current state.
        - legal_actions(): compute list of valid actions for current player.
    """

class CommandLineUI:
    """
    Text-based UI for human or DEBUG play in a terminal.

    Responsibilities:
        - Display board and player states in ASCII.
        - Prompt human for action selection by index.
        - Show invalid-action errors and re-prompt.
    """

class RandomAgent:
    """
    An agent that chooses uniformly at random among legal actions.

    Responsibilities:
        - query the env’s .legal_actions().
        - select and return a random Action instance on request.
    """