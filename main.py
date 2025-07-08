import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

import discord
from discord.ext import commands
from dotenv import load_dotenv

GUILD_ID = 1392183899945177180  # Replace with your actual guild ID (as int)
guild = discord.Object(id=GUILD_ID)

# SSL fix

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} - Ready to command the empire!")
    await bot.tree.sync(guild=guild)


import commands  # your commands file

async def main():
    async with bot:
        await commands.setup(bot)
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
