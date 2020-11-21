import discord
import os
from random import shuffle
from datetime import datetime
from typing import List
from enum import Enum

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
EMBED_COLOR = 0x277714

CHECK_EMOJI = ":white_check_mark:"
CALL_EMOJI = ":cl:"
RAISE_EMOJI = ":arrow_up:️"
FOLD_EMOJI = ":no_entry_sign:"

CHECK_EMOJI_RAW = "✅"
CALL_EMOJI_RAW = "🆑"
RAISE_EMOJI_RAW = "⬆️"
FOLD_EMOJI_RAW = "🚫"

DEALER_EMOJI = ":radio_button:"
BIG_BLIND_EMOJI = ":moneybag:"
SMALL_BLIND_EMOJI = ":dollar:"

TURN_EMOJI = ":arrow_right:"
NORMAL_EMOJI = ":blue_square:"


class TurnTypes(Enum):
    CHECK, CALL, RAISE, FOLD = range(4)

    def __str__(self):
        return self.name.lower() + "s"

    def emoji(self):
        return [CHECK_EMOJI, CALL_EMOJI, RAISE_EMOJI, FOLD_EMOJI][self.value]


class LogEntry:
    def __init__(self, arg1, turn_type=None, raise_amount=0):
        self.arg1 = arg1 # player, or manual log entry string
        self.player = arg1
        self.turn_type = turn_type
        self.raise_amount = raise_amount

    def __str__(self):
        if isinstance(self.arg1, str):
            return self.arg1

        s = self.player.mention + " " + str(self.turn_type)
        if self.turn_type == TurnTypes.RAISE:
            s += " to " + str(self.raise_amount)
        return s + "."


class PlayerTypes(Enum):
    DEALER, BIG_BLIND, SMALL_BLIND, NORMAL = range(4)

    def emoji(self):
        return [DEALER_EMOJI, BIG_BLIND_EMOJI, SMALL_BLIND_EMOJI, ""][self.value]


def load_emojis(client):
    global EMOJIS_LOADED, EMOJIS
    if EMOJIS_LOADED:
        return

    card_server = client.get_guild(EMOJI_SERVER_ID)
    EMOJIS = card_server.emojis

    EMOJIS_LOADED = True


def card_to_emojis(card):
    suit1 = "b" if card.suit.name[0] in "SC" else "r"
    suit2 = card.suit.name.lower()
    rank_num = card.rank.value + 1
    if rank_num == 1:
        rank = "A"
    elif rank_num > 10:
        rank = "JQK"[rank_num - 11]
    else:
        rank = str(rank_num)

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


"""
raising works like this:
  - initially react with up arrow to begin raise
  - new reacts: <-- to decrease, --> to increase (and cancel to cancel) 
    and only increment by minimum allowed amount
"""
# TODO: organize functions into files
# TODO: calculate winner
# TODO: new raise interface (described above)
# TODO: negative betting fix
# TODO: log scrolling
# TODO: game customization (minimum bet, initial balance)
# TODO: intergame balance storing
# TODO: all in


class Player:
    def __init__(self, game, user, hand, balance):
        self.game = game
        self.user = user
        self.type = PlayerTypes.NORMAL
        self.hand = hand
        self.message_id = -1
        self.balance = balance
        self.mention = user.mention
        self.folded = False

    async def send(self, *args, **kwargs):
        return await self.user.send(*args, **kwargs)


class Game:
    def __init__(self, players: List[discord.User], client: discord.Client, init_bal=1000):
        self.client = client
        self.players = [Player(self, player, [], init_bal) for player in players]
        self.deck = Deck().shuffle()
        self.table = []
        self.turn_order = self.players[:]
        self.active = True
        self.action_log = []
        shuffle(self.turn_order)
        load_emojis(client)

    def reshuffle(self):
        self.deck = Deck().shuffle()

    async def deal_to_all(self):
        for player in self.players:
            cards = [self.deck.deal() for _ in range(PLAYER_HAND_SIZE)]
            player.hand = cards

    async def send_embed(self, turn=0, pot=0):
        # generated with https://discohook.org/ and https://leovoel.github.io/embed-visualizer/
        for player in self.players:
            embed = discord.Embed(colour=discord.Colour(EMBED_COLOR),
                                  description="Welcome to Poker! In this window, you'll be able to see the "
                                              "cards on the table and in your hand, the turn order, and "
                                              "the action log. Good luck!",
                                  timestamp=datetime.utcnow())

            embed.set_author(name="Poker Game Alpha",
                             icon_url="https://cdn.discordapp.com/avatars/734515824051617813/"
                                      "4cb69fdb5cc46c88b81aaecf44703b0f.png?size=256")
            embed.set_footer(text="Last updated")

            blanks = 5 - len(self.table)
            embed.add_field(name="On the Table",
                            value=cards_to_str(self.table, blanks=blanks) + f"\nPot: {pot}", inline=True)
            embed.add_field(name="In Your Hand",
                            value=cards_to_str(player.hand) + f"\nBalance: {player.balance}", inline=True)

            hand_type, cards = detect_hand(self.table + player.hand)
            embed.add_field(name=f"You have a {hand_type.real_name()}:", value=cards_to_str(cards), inline=True)

            max_logs = 4
            log = "\n".join(map(str, self.action_log[-max_logs:])) if self.action_log else "Nothing here yet..."
            log += f"\nPage {len(self.action_log) // max_logs} / {len(self.action_log) // max_logs}\n\n" \
                   f"React with :arrow_left: and :arrow_right: to scroll."
            # TODO

            embed.add_field(name="Log", value=log, inline=True)

            turn_str = ""
            for i, p in enumerate(self.turn_order):
                turn_emoji = TURN_EMOJI if i == turn else NORMAL_EMOJI
                mention = "~~" + p.mention + "~~" if p.folded else p.mention
                turn_str += f"{turn_emoji} {mention} {p.type.emoji()}\n"

            embed.add_field(name="Turn Order",
                            value=turn_str + f"\n{TURN_EMOJI} = current turn\n{DEALER_EMOJI} = dealer\n"
                                             f"{BIG_BLIND_EMOJI} = big blind\n{SMALL_BLIND_EMOJI} = small blind",
                            inline=True)

            if player.message_id == -1:
                msg = await player.send(embed=embed)
                player.message_id = msg.id
            else:
                msg = discord.utils.get(self.client.cached_messages, id=player.message_id)
                await msg.edit(embed=embed)

    async def flip(self):
        assert len(self.table) < TABLE_SIZE, "can't show more than 5 cards"

        is_flop = (len(self.table) == 0)
        num_cards = FLOP_SIZE if is_flop else 1

        for _ in range(num_cards):
            self.table.append(self.deck.deal())

    async def send_to_all(self, msg, *but):
        for p in self.players:
            if p not in but:
                await p.send(msg)

    async def round(self):
        pot = 0
        bets = {player: 0 for player in self.players}

        dealer = self.turn_order[0]
        if len(self.turn_order) == 2:
            first = 0
            small_blind = self.turn_order[0]
            big_blind = self.turn_order[1]
        else:
            first = 3
            small_blind = self.turn_order[1]
            big_blind = self.turn_order[2]

        # TODO: constants
        bets[small_blind] = 5
        small_blind.balance -= 5
        bets[big_blind] = 10
        big_blind.balance -= 10

        pot += 15
        dealer.type = PlayerTypes.DEALER
        small_blind.type = PlayerTypes.SMALL_BLIND
        big_blind.type = PlayerTypes.BIG_BLIND

        self.action_log.append(LogEntry(f"{dealer.mention} deals."))
        self.action_log.append(LogEntry(f"{big_blind.mention} places 10 as the big blind."))
        self.action_log.append(LogEntry(f"{small_blind.mention} places 5 as the small blind."))

        await self.send_embed(first, pot)

        msgs = {}
        for player in self.players:
            msgs[player] = discord.utils.get(self.client.cached_messages, id=player.message_id)

        pre_flop = True

        while len(self.table) <= 5:
            turn = first % len(self.turn_order)
            player = self.turn_order[turn]
            bets = bets if pre_flop else {player: 0 for player in self.players}
            bet_now = bets[big_blind] if pre_flop else 0
            # has_had_turn = {player: False for player in self.turn_order}
            first_turn = True
            last_raiser = player

            await self.send_embed(turn, pot)

            while last_raiser != player or first_turn:
                if player.folded:
                    turn += 1
                    turn %= len(self.turn_order)
                    player = self.turn_order[turn]
                    await self.send_embed(turn, pot)
                    continue

                is_check = (bet_now == bets[player])

                temp_msg = await player.send(f"It is your turn! {CHECK_EMOJI if is_check else CALL_EMOJI} = "
                                             f"{'check' if is_check else 'call'}, "
                                             f"{RAISE_EMOJI}️ = raise, {FOLD_EMOJI} = fold")
                await temp_msg.add_reaction(CHECK_EMOJI_RAW if is_check else CALL_EMOJI_RAW)
                await temp_msg.add_reaction(RAISE_EMOJI_RAW)
                await temp_msg.add_reaction(FOLD_EMOJI_RAW)

                def check(rxn, usr):
                    return str(rxn.emoji) in [(CHECK_EMOJI_RAW if is_check else CALL_EMOJI_RAW),
                                              RAISE_EMOJI_RAW, FOLD_EMOJI_RAW] \
                           and rxn.message.id == temp_msg.id and usr.id == player.user.id

                reaction, user = await self.client.wait_for('reaction_add', check=check)
                emoji = str(reaction.emoji)

                if emoji == FOLD_EMOJI_RAW:
                    self.action_log.append(LogEntry(player, TurnTypes.FOLD))
                    player.folded = True

                elif emoji == CHECK_EMOJI_RAW:
                    self.action_log.append(LogEntry(player, TurnTypes.CHECK))

                elif emoji == CALL_EMOJI_RAW:
                    change = bet_now - bets[player]
                    player.balance -= change
                    bets[player] = bet_now
                    pot += change
                    self.action_log.append(LogEntry(player, TurnTypes.CALL))

                elif emoji == RAISE_EMOJI_RAW:
                    await player.send("How much would you like to raise to?")

                    def check(m):
                        try:
                            return int(m.content) >= bet_now + 10
                        except ValueError:
                            return False

                    message = await self.client.wait_for('message', check=check)
                    bet_now = int(message.content)
                    change = bet_now - bets[player]
                    bets[player] = bet_now
                    pot += change
                    last_raiser = player
                    self.action_log.append(LogEntry(player, TurnTypes.RAISE, bet_now))

                else:
                    print("Something went wrong, no correct reactions")

                await temp_msg.delete()
                turn += 1
                turn %= len(self.turn_order)
                player = self.turn_order[turn]
                first_turn = False
                await self.send_embed(turn, pot)

            if len(self.table) == 5:
                break

            await self.flip()

            if pre_flop:
                self.action_log.append(LogEntry(english_list(self.table[-3:]) + " revealed."))
            else:
                self.action_log.append(LogEntry(str(self.table[-1]) + " revealed."))

            pre_flop = False
            first = 1
            await self.send_embed(turn, pot)

        hands = {player: detect_hand(player.hand + self.table) for player in self.turn_order}

        await self.send_to_all(english_list([player.mention + " has " + hands[player][0].name
                                             for player in self.turn_order]))
        self.active = False
