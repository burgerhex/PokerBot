import discord
import os
import random
from helpers import *
from poker.cards import Deck


client = discord.Client(request_offline_members=False)
TOKEN = os.environ.get("BOT_TOKEN")


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
    id = message.id

    # don't respond to self, don't respond to non-commands, and don't respond to DMs
    if author == client.user or not is_command(msg) or not guild:
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


    elif cmd in ["game"]:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            author: discord.PermissionOverwrite(read_messages=True)
        }

        name = " ".join(args) if args else 1

        category = await guild.create_category(f"Poker Game {name}", overwrites=overwrites)
        game = await guild.create_text_channel("game", category=category)
        chat = await guild.create_text_channel("chat", category=category)
        voice = await guild.create_voice_channel("voice", category=category)

        await send("Created category and channels!")


    elif cmd in ["delete", "del"]:
        for channel in guild.channels[::-1]:
            if isinstance(channel, discord.CategoryChannel) and channel.name.lower().startswith("poker game"):
                for subchannel in channel.channels[::-1]:
                    await subchannel.delete()
                await channel.delete()

        await send("Deleted game channels!")


    elif cmd in ["card"]:
        deck = Deck().shuffle()
        card = deck.deal()
        await channel.send(f"Your card is the {card}.")


    elif cmd in ["war"]:
        deck = Deck().shuffle()
        card1 = deck.deal()
        card2 = deck.deal()
        winner = 1 if card1 > card2 else 2
        await channel.send(f"Card 1 is {card1}, and card 2 is {card2}. Card {winner} wins!")


client.run(TOKEN)
