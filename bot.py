import discord
import os

client = discord.Client()

is_prod = os.environ.get('IS_HEROKU', None)

if not is_prod:
    print("Not in Heroku, no token, aborting...")
    exit(1)


TOKEN = os.environ.get("BOT_TOKEN")


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


client.run(TOKEN)
