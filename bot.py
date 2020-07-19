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
    print(f"{client.user} has connected to Discord!")


client.run(TOKEN)
