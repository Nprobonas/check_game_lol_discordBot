import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
from typing import Optional
from dotenv import load_dotenv
import urllib.parse


# Charger les variables d'environnement
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Intents Discord
intents = discord.Intents.default()
intents.message_content = True

# Création du bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Event du démarrage du bot
@bot.event
async def on_ready():
    print(f'{bot.user} le Krab jusiticer est connecté !')

async def main():
    #Endroit pour charger les Cogs Discord
    await bot.load_extension("cogs.lookup_cog")
    await bot.load_extension("cogs.clown_cog")
    await bot.load_extension("cogs.price_watcher_cog")
    await bot.load_extension("cogs.fng_cog")
    await bot.load_extension("cogs.free_games_cog")
    print("Cogs chargés avec succès !")
    
    # Start du bot via le token Discord
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Déconnexion \nKrabinoche retourne dans les abysses..")