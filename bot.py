import discord
import os
import random
from asyncio import sleep
from helpers import *
from poker.game import Game


client = discord.Client(request_offline_members=False)
TOKEN = os.environ.get("BOT_TOKEN")

JOIN_TIMEOUT = 8
MAX_PLAYERS = 8

games = []


@client.event
async def on_ready():
    print(f"Successfully logged in as {client.user} with ID {client.user.id}")


@client.event
async def on_message(message):
    guild = message.guild
    channel = message.channel
    send = channel.send # this is a function
    author = message.author
    msg = message.content

    # clear empty games
    global games
    games = [game for game in games if game.active]

    # don't respond to self
    if author == client.user or not is_command(msg):
        return

    print(f"Received command attempt \"{msg}\" from {author} in {channel} in {guild}")

    parts = extract_parts(msg)
    cmd = parts[0]
    args = parts[1:]


    if cmd in ["hello", "hi", "hey"]:
        await send(f"Hello, {author.mention}! :smile:")


    elif cmd in ["where", "whereami"]:
        await send(f"We are in the server **{guild.name}** in the channel {channel.mention}! :smile:")


    elif cmd in ["die", "dice"]:
        await send(f"Rolled a {random.choice(range(1, 6))}.")


    elif cmd in ["coin", "coinflip"]:
        await send(f"Flipped {'Heads' if (random.random() > 0.5) else 'Tails'}.")


    # TODO: disallow people already in games
    elif cmd in ["game", "startgame", "start"]:
        pre_message = f"{author.mention} is starting a poker game! React to this message to join! "
        game_message = await send(pre_message + f"{JOIN_TIMEOUT} seconds left!")
        await game_message.add_reaction("✅")

        await sleep(JOIN_TIMEOUT / 4)

        for i in range(3, 0, -1):
            await game_message.edit(content=pre_message + f"{i / 4 * JOIN_TIMEOUT} seconds left!")
            await sleep(JOIN_TIMEOUT / 4)

        reactors = [author]
        cache_msg = discord.utils.get(client.cached_messages, id=game_message.id)

        for reaction in cache_msg.reactions:
            async for user in reaction.users():
                if user.id not in [r.id for r in reactors] and user != client.user:
                    reactors.append(user)
                if len(reactors) == MAX_PLAYERS:
                    break
            else:
                continue
            break

        if len(reactors) < 2:
            await game_message.edit(content=f"Not enough players reacted; the game is cancelled. :slight_frown:")
            await game_message.clear_reactions()
            return

        await game_message.edit(content=f"{author.mention} has started a poker game! "
                                        f"Players: {english_list(reactors, lambda r: r.mention)}")
        await game_message.clear_reactions()

        game = Game(reactors, client)
        games.append(game)
        await game.deal_to_all()
        await game.round()


    elif cmd in ["game?"]:
        game = discord.utils.find(lambda g: author in g.players, games)

        if game:
            players_but = [p for p in game.players if p != author]
            await send(f"You are in a game with {english_list(players_but, lambda p: p.mention)}.")
        else:
            await send("You are not currrently in a game.")


client.run(TOKEN)
