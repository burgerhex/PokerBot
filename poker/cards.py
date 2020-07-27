from enum import Enum
from helpers import capitalize
from random import shuffle

NUM_SUITS = 4
NUM_RANKS = 13
CARDS_IN_DECK = 52


# enums because i'm extra and want to emulate java :)
class Suit(Enum):
    DIAMONDS, HEARTS, CLUBS, SPADES = range(NUM_SUITS)


class Rank(Enum):
    ACE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, \
        NINE, TEN, JACK, QUEEN, KING = range(NUM_RANKS)


class Card:
    def __init__(self, s: Suit, r: Rank):
        assert isinstance(s, Suit) and isinstance(r, Rank), \
            "must pass in Suit and Rank objects to initialize a Card"
        self.suit = s
        self.rank = r


    def __str__(self):
        return capitalize(self.rank.name) + " of " + capitalize(self.suit.name)


    def __lt__(self, other):
        assert isinstance(other, Card), "operator < must be used with two Cards"
        if self.rank != other.rank:
            return self.rank.value < other.rank.value
        else:
            return self.suit.value < other.suit.value


    def __gt__(self, other):
        assert isinstance(other, Card), "operator > must be used with two Cards"
        if self.rank != other.rank:
            return self.rank.value > other.rank.value
        else:
            return self.suit.value > other.suit.value


    def __eq__(self, other):
        assert isinstance(other, Card), "operator == must be used with two Cards"
        return not (self < other or self > other)


class Deck:
    def __init__(self):
        self.cards = []

        for s in Suit:
            for r in Rank:
                self.cards.append(Card(s, r))

        assert len(self.cards) == NUM_SUITS * NUM_RANKS == CARDS_IN_DECK, "deck is invalid"


    def shuffle(self):
        shuffle(self.cards)
        return self


    def deal(self):
        return self.cards.pop() if self.cards else None


    def __str__(self):
        return str(list(map(str, self.cards)))
