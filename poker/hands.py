# all of these functions return False if the associated hand is not present,
# and return the cards that create the hand if it is present
from enum import Enum
from poker.cards import Rank

NUM_HANDS = 10


class PokerHand(Enum):
    HIGH_CARD, PAIR, TWO_PAIR, THREE_KIND, STRAIGHT, FLUSH, FULL_HOUSE, \
        FOUR_KIND, STRAIGHT_FLUSH, ROYAL_FLUSH = range(NUM_HANDS)


def has_royal_flush(hand):
    if len(hand) < 5:
        return False

    s_flush = has_straight_flush(hand)
    if not s_flush:
        return False

    ranks = [c.rank for c in s_flush]

    if Rank.KING in ranks and Rank.ACE in ranks:
        return s_flush
    else:
        return False


def has_straight_flush(hand):
    if len(hand) < 5:
        return False

    flush = has_flush(hand)
    if not flush:
        return False

    suit = flush[0].suit
    hand_suit = [c for c in hand if c.suit == suit]

    straight = has_straight(hand_suit)
    if not straight:
        return False

    return straight


def has_four_kind(hand):
    return has_group(hand, 4)


def has_full_house(hand):
    if len(hand) < 5:
        return False

    three = has_three_kind(hand)
    if not three:
        return False

    rank3 = three[0].rank
    hand_no3 = [c for c in hand if c.rank != rank3]

    pair = has_pair(hand_no3)
    if not pair:
        return False

    return three + pair


def has_flush(hand):
    if len(hand) < 5:
        return False

    suits = [c.suit.value for c in hand]
    appearances = {suit: suits.count(suit) for suit in set(suits)}
    flushes = {suit: count for suit, count in appearances.items() if count >= 5}

    if len(flushes) == 0:
        return False

    hand_s = list(sorted(hand, key=lambda c: -c.rank.value))
    # move aces to front
    num_aces = len([c for c in hand_s if c.rank == Rank.ACE])
    hand_s = hand_s[-num_aces:] + hand_s[:-num_aces]

    for card in hand_s:
        if card.suit.value in flushes:
            this_suit = [c for c in hand_s if c.suit == card.suit]
            return this_suit[:5]


def has_straight(hand):
    if len(hand) < 5:
        return False

    ranks = [c.rank.value for c in hand]
    ranks_s = sorted(set(ranks))

    for i in range(len(ranks_s) - 3)[::-1]:
        if (i < len(ranks_s) - 4 and all([ranks_s[i + j] + 1 == ranks_s[i + j + 1] for j in range(4)])) or \
                (all([ranks_s[i + j] == Rank.TEN.value + j for j in range(4)]) and Rank.ACE.value in ranks_s):
            # have to check 10-A straight separately ^
            lowest = ranks_s[i]
            to_get = list(range(lowest, lowest + 5)) if lowest != Rank.TEN.value \
                else [*range(Rank.TEN.value, Rank.TEN.value + 4), Rank.ACE.value]

            cards = []
            for c in hand:
                if c.rank.value in to_get:
                    cards.append(c)
                    to_get.remove(c.rank.value)

            cards = list(sorted(cards, key=lambda c: c.rank.value))
            if lowest == Rank.TEN.value:
                cards = cards[1:] + cards[:1]

            return cards

    return False


def has_three_kind(hand):
    return has_group(hand, 3)


def has_two_pair(hand):
    if len(hand) < 4:
        return False

    ranks = [c.rank.value for c in hand]
    appearances = {rank: ranks.count(rank) for rank in set(ranks)}
    pairs = {rank: count for rank, count in appearances.items() if count >= 2}

    if len(pairs) < 2:
        return False

    pair_ranks = sorted(pairs.keys())[::-1]
    highest1, highest2 = pair_ranks[:2]

    cards1 = [c for c in hand if c.rank.value == highest1]
    cards2 = [c for c in hand if c.rank.value == highest2]

    return cards1[:2] + cards2[:2]


def has_pair(hand):
    return has_group(hand, 2)


# detects pair (two of a kind), three of a kind, and four of a kind all in one
def has_group(hand, group_size):
    if len(hand) < group_size:
        return False

    ranks = [c.rank.value for c in hand]
    appearances = {rank: ranks.count(rank) for rank in set(ranks)}
    groups = {rank: count for rank, count in appearances.items() if count >= group_size}

    if len(groups) == 0:
        return False

    group_ranks = sorted(groups.keys())[::-1]
    highest_rank = Rank.ACE.value if Rank.ACE.value in group_ranks else group_ranks[0]

    cards_of_rank = [c for c in hand if c.rank.value == highest_rank]

    return cards_of_rank[:group_size]


def detect_hand(hand):
    hand_funcs = [has_royal_flush, has_straight_flush, has_four_kind, has_full_house,
                  has_flush, has_straight, has_three_kind, has_two_pair, has_pair]

    for hand_num in range(NUM_HANDS):
        if hand_num == NUM_HANDS - 1:
            if Rank.ACE in [c.rank for c in hand]:
                m = [c for c in hand if c.rank == Rank.ACE][0]
            else:
                m = max(hand, key=lambda c: c.rank.value)

            return PokerHand.HIGH_CARD, [m]

        func = hand_funcs[hand_num]
        found = func(hand)
        if found:
            return PokerHand(NUM_HANDS - hand_num - 1), found
