import discord
import os
from random import shuffle
from typing import List

from helpers import english_list
from poker.cards import Deck
from poker.hands import detect_hand

EMOJIS_LOADED = False
# server that has card emojis
EMOJI_SERVER_ID = int(os.environ.get("EMOJI_SERVER_ID"))
EMOJIS = []

PLAYER_HAND_SIZE = 2
FLOP_SIZE = 3
TABLE_SIZE = 5

CALL_EMOJI = "🆑"
CHECK_EMOJI = "✅"
RAISE_EMOJI = "⬆️"
FOLD_EMOJI = "🚫"


def load_emojis(client):
    global EMOJIS_LOADED, EMOJIS
    if EMOJIS_LOADED:
        return

    card_server = client.get_guild(EMOJI_SERVER_ID)
    EMOJIS = card_server.emojis

    EMOJIS_LOADED = True


def card_to_emojis(card):
    suit1 = "b" if card.suit.name[0] in ["S", "C"] else "r"
    suit2 = card.suit.name.lower()
    rank = card.rank.value + 1
    rank = "A" if rank == 1 else ["J", "Q", "K"][rank - 11] if rank > 10 else str(rank)

    emoji1 = discord.utils.get(EMOJIS, name=suit1 + rank)
    emoji2 = discord.utils.get(EMOJIS, name="e" + suit2)

    return emoji1, emoji2


def emojis_to_str(ems, join=" ", sep="\n"):
    top = btm = ""

    for up, down in ems:
        top += str(up) + join
        btm += str(down) + join

    return top + sep + btm


def cards_to_str(cards, join=" ", sep="\n", blanks=0):
    blank_top = discord.utils.get(EMOJIS, name="blankbacktop")
    blank_btm = discord.utils.get(EMOJIS, name="blankbackbot")
    emojis = [card_to_emojis(c) for c in cards] + [(blank_top, blank_btm)] * blanks
    return emojis_to_str(emojis, join, sep)


class Player:
    def __init__(self, game, user, hand, message_id, balance):
        self.game = game
        self.user = user
        self.hand = hand
        self.message_id = message_id
        self.balance = balance
        self.mention = user.mention

    async def send(self, *args, **kwargs):
        return await self.user.send(*args, **kwargs)


class Game:
    def __init__(self, players: List[discord.User], client: discord.Client, init_bal=1000):
        self.client = client
        self.players = [Player(self, player, [], -1, init_bal) for player in players]
        self.deck = Deck().shuffle()
        self.table = []
        self.turn_order = self.players[:]
        self.active = True
        shuffle(self.turn_order)
        load_emojis(client)

    def reshuffle(self):
        self.deck = Deck().shuffle()

    async def deal_to_all(self):
        for player in self.players:
            cards = [self.deck.deal() for _ in range(PLAYER_HAND_SIZE)]
            player.hand = cards
            message = await player.send("Your cards:\n" + cards_to_str(cards))
            player.message_id = message.id

    async def flip(self):
        assert len(self.table) < TABLE_SIZE, "can't show more than 5 cards"

        is_flop = (len(self.table) == 0)
        is_turn = (len(self.table) == FLOP_SIZE)

        for _ in range(FLOP_SIZE if is_flop else 1):
            self.table.append(self.deck.deal())

        for p in self.players:
            # msg = discord.utils.get(self.client.cached_messages, id=p.message_id)
            # mode = "Flop" if is_flop else "Turn" if is_turn else "River"
            # await msg.edit(content="Your cards:\n" + cards_to_str(p.hand) + "\n" + mode + ":\n" +
            #                        cards_to_str(self.table, blanks=TABLE_SIZE - len(self.table)))
            await p.send(content="Your cards:\n" + cards_to_str(p.hand) + "\nOn the table:\n" +
                                 cards_to_str(self.table, blanks=TABLE_SIZE - len(self.table)))

    async def send_to_all(self, msg, *but):
        for p in self.players:
            if p not in but:
                await p.send(msg)

    async def round(self):
        pot = 0
        bets = {player: 0 for player in self.players}

        round_players = self.turn_order[:]

        dealer = round_players[0]
        if len(round_players) == 2:
            first = 0
            small_blind = round_players[0]
            big_blind = round_players[1]
        else:
            first = 3
            small_blind = round_players[1]
            big_blind = round_players[2]

        bets[small_blind] = 5
        small_blind.balance -= 5
        bets[big_blind] = 10
        big_blind.balance -= 10

        await self.send_to_all(f"{dealer.mention} is the dealer, {small_blind.mention} has placed 5 as the "
                               f"small blind, and {big_blind.mention} has placed 10 as the big blind.")

        pre_flop = True

        while True:
            turn = first
            bets = bets if pre_flop else {player: 0 for player in self.players}
            bet_now = bets[big_blind] if pre_flop else 0
            has_had_turn = {player: False for player in round_players}

            while len(set(bets.values())) > 1 or not all(has_had_turn.values()):
                player = round_players[turn % len(round_players)]
                has_had_turn[player] = True

                is_check = (bet_now == bets[player])

                await self.send_to_all(f"It is {player.mention}'s turn.", player)
                msg = await player.send(f"It is your turn. React with {CHECK_EMOJI if is_check else CALL_EMOJI} to "
                                        f"{'check' if is_check else 'call'} the current bet of {bet_now}, {RAISE_EMOJI}️ "
                                        f"to raise, or {FOLD_EMOJI} to fold. You have {player.balance} chips.")
                await msg.add_reaction(CHECK_EMOJI if is_check else CALL_EMOJI)
                await msg.add_reaction(RAISE_EMOJI)
                await msg.add_reaction(FOLD_EMOJI)

                def check(rxn, usr):
                    return str(rxn.emoji) in [(CHECK_EMOJI if is_check else CALL_EMOJI), RAISE_EMOJI, FOLD_EMOJI] \
                           and rxn.message.id == msg.id and usr.id == player.user.id

                reaction, user = await self.client.wait_for('reaction_add', check=check)

                if str(reaction.emoji) == FOLD_EMOJI:
                    await player.send("You have folded this round.")
                    await self.send_to_all(f"{player.mention} folds.", player)
                    round_players.remove(player)
                    del bets[player]
                    turn -= 1

                elif str(reaction.emoji) == (CHECK_EMOJI if is_check else CALL_EMOJI):
                    player.balance -= bet_now - bets[player]
                    bets[player] = bet_now
                    await player.send(("You have checked. " if is_check else
                                       f"You have called the current bet of {bet_now}. ") +
                                      f"You now have {player.balance} chips left.")
                    await self.send_to_all(f"{player.mention} calls.", player)

                elif str(reaction.emoji) == RAISE_EMOJI:
                    await player.send("How much would you like to raise to?")

                    def check(m):
                        try:
                            return int(m.content) >= bet_now + 10
                        except ValueError:
                            return False

                    message = await self.client.wait_for('message', check=check)
                    bet_now = int(message.content)
                    player.balance -= bet_now - bets[player]
                    bets[player] = bet_now
                    await player.send(f"You have raised the current bet to {bet_now}. "
                                      f"You now have {player.balance} chips left.")
                    await self.send_to_all(f"{player.mention} raises to {bet_now}.", player)

                else:
                    print("Something went wrong, no correct reactions")

                turn += 1

            await self.send_to_all("This round is over.")
            pre_flop = False
            if len(self.table) == 5:
                break
            else:
                await self.flip()
            first = 1

        hands = {player: detect_hand(player.hand + self.table) for player in round_players}

        await self.send_to_all(english_list([player.mention + " has " + hands[player][0].name
                                             for player in round_players]))
        self.active = False
