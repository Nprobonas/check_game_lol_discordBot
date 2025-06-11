import discord
from discord.ext import commands
import asyncio
import os
import requests
from dotenv import load_dotenv

load_dotenv()
CMC_API_KEY=os.getenv('CMC_API_KEY')

class Fng(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://pro-api.coinmarketcap.com/v2"
        self.api_key = os.getenv('CMC_API_KEY')
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
        
        }
        
    @commands.command(name='fng')
    async def fear_and_greed(self, ctx):
        """Commande d'affichage de l'index fear and greed"""
        try:
            r = requests.get("https://api.alternative.me/fng/")
            r.raise_for_status()
            data = r.json()
            value = data["data"][0]["value"]
            label = data["data"][0]["value_classification"]

            fg_emojis = {
                "Extreme Fear": "😱",
                "Fear": "😨",
                "Neutral": "😐",
                "Greed": "🤑",
                "Extreme Greed": "🤩"
            }
            emoji = fg_emojis.get(label, "")
            embed = discord.Embed(
                title="Crypto Fear & Greed Index",
                description=f"{emoji} **{value}** – {label}",
                color=0x4682B4
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la récupération du F&G index.\n{e}")
            
async def setup(bot):
    await bot.add_cog(Fng(bot))