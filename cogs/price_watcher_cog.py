from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime
import requests
import time
from pathlib import Path
import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
CMC_API_KEY=os.getenv('CMC_API_KEY')

@dataclass
class CryptoPriceWatcher():
    price: float
    change_24h: float
    change_7d: float
    volume_24h: float
    market_cap: float
    timestamp: datetime


class PriceMonitorBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://pro-api.coinmarketcap.com/v2"
        self.api_key = os.getenv('CMC_API_KEY')
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
        
        }

    def get_crypto_info(self, symbol: str) -> Optional[CryptoPriceWatcher]:
        endpoint = "/cryptocurrency/quotes/latest"
        params = {
            'symbol': symbol,
            'convert': 'USD'
        }
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

            # On cherche le vrai Bitcoin (id: 1) dans la liste des résultats -> pour toutes les autres paires init à 0.
            crypto_raw = data['data'][symbol]
            if isinstance(crypto_raw, list):
                crypto_data = crypto_raw[0]
            elif isinstance(crypto_raw, dict):
                crypto_data = crypto_raw
            else:
                print("Problème avec API:", type(crypto_raw))
                return None
        
            if crypto_data:
                quote = crypto_data['quote']['USD']
                return CryptoPriceWatcher(
                    price=quote['price'],
                    change_24h=quote['percent_change_24h'],
                    change_7d=quote['percent_change_7d'],
                    volume_24h=quote['volume_24h'],
                    market_cap=quote['market_cap'],
                    timestamp=datetime.strptime(
                        quote['last_updated'],
                        '%Y-%m-%dT%H:%M:%S.%fZ'
                    )
                )
            return None
                
        
        except Exception as e:
            print(f"Erreur lors de la requête: {e}")
            return None


    def get_crypto_logo(self, symbol):
        endpoint = "/cryptocurrency/info"
        params = {'symbol': symbol}
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            symbol_data = data['data'][symbol]
            if isinstance(symbol_data, list):
                logo_url = symbol_data[0]['logo']
            elif isinstance(symbol_data,dict):
                logo_url = symbol_data['logo']
            else:
                logo_url = None
            return logo_url
        except Exception as e:
            print(f"Erreur lors de la récupération du logo : {e}")
            return None


    def analyze_market_sentiment(self, info: CryptoPriceWatcher) -> str:
        """ Analyse simple du sentiment du marché """
        sentiment = []
        
        # Analyse du prix et des variations
        if info.change_24h > 5:
            sentiment.append("🚀 Fort mouvement haussier sur 24h")
        elif info.change_24h < -5:
            sentiment.append("📉 Fort mouvement baissier sur 24h")
            
        if info.change_7d > 10:
            sentiment.append("📈 Tendance très positive sur 7 jours")
        elif info.change_7d < -10:
            sentiment.append("⚠️ Tendance très négative sur 7 jours")
            
        # Analyse du volume
        if info.volume_24h > info.market_cap * 0.1:
            sentiment.append("💫 Volume important, forte activité")
            
        return "\n".join(sentiment) if sentiment else "😐 Marché stable"
    
    
    # Init des commandes
    # Debug
        #print("Commande !price appelée avec:", symbol)
        #await ctx.send("Debug: commande appelée")
        
    @commands.command(name='price')
    async def price(self, ctx, *symbols):
        """Commande d'affichage en temps réel du prix du BTC"""
        if not symbols:
            await ctx.send("Il faut au moins un symbole afin de lancer la recherche, exemple -> !price ETH")
            return

        for symbol in symbols:
           # print(f"[DEBUG] Recherche symbol: {symbol}")
            data = self.get_crypto_info(symbol.upper())
            logo_url = self.get_crypto_logo(symbol.upper())
           # print(f"[DEBUG] Résult data : {data}")
           # print(f"[DEBUG] Result logo_url: {logo_url}")
            
            if data:
                sentiment = self.analyze_market_sentiment(data)
                embed = discord.Embed(
                    title=f"Prix du {symbol.upper()}",
                    description=f"**Prix :** {data.price:,.2f} $",
                    color= 0x4682B4 # Bleu acier
                )
                if logo_url:
                    embed.set_thumbnail(url=logo_url)
                    
                embed.add_field(name="Variation 24h", value=f"{data.change_24h:+.2f} %")
                embed.add_field(name="Variation 7j", value=f"{data.change_7d:+.2f} %")
                embed.add_field(name="Volume 24h", value=f"{data.volume_24h:,.0f} $")
                embed.add_field(name="Market Cap", value=f"{data.market_cap:,.0f} $")
                embed.add_field(name="Sentiment", value=sentiment, inline=False)
                embed.set_footer(text=f"Dernière mise à jour : {data.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Erreur API -> Impossible de récupérer le prix pour {symbol.upper()}. \n Essaye !price SOL")
        
        
    @commands.command(name='help_price')
    async def help_price(self,ctx):
        embed = discord.Embed(
            title="Commandes du watcher prix cryptos",
            description="**IMPORTANT** :  Utilise !price [nom_crypto] afin d'afficher le prix et le sentiment du marché",
            color=0x00ff00
        )
        embed.add_field(
            name="!price SOL",
            value="Affiche les informations et le sentiment du marché sur un symbol crypto",
            inline=False
    )
        await ctx.send(embed=embed)
            
        
    # @price.error
    # async def price_error(self, ctx, error):
    #     if isinstance(error, commands.CommandOnCooldown):
    #         await ctx.send(f"🕒 Arrête de spam bâtard ! Attends {error.retry_after:.1f} secondes avant de réutiliser !price.")
        


async def setup(bot):
  await bot.add_cog(PriceMonitorBot(bot))
