import discord
import os
import requests
import asyncio
import urllib.parse
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from typing import Optional


load_dotenv()
RIOT_API_KEY = os.getenv('RIOT_API_KEY')



class RiotAPI(commands.Cog):
    
    def __init__(self, bot, api_key: str):
        self.bot = bot
        self.api_key = api_key
        self.account_base_url = "https://europe.api.riotgames.com"
        self.summoner_base_url = "https://euw1.api.riotgames.com"
        self.headers = {"X-Riot-Token": api_key}

    async def get_puuid_by_riot_id(self, game_name: str, tag_line: str) -> Optional[str]:
        url = f"{self.account_base_url}/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(game_name)}/{urllib.parse.quote(tag_line)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("puuid")
                else:
                    print(f"Erreur Riot ID API : status {response.status} url {url}")
                    print(await response.text())
                    return None

    async def get_summoner_by_puuid(self, puuid: str) -> Optional[dict]:
        url = f"{self.summoner_base_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Erreur Summoner API : status {response.status} url {url}")
                    print(await response.text())
                    return None

    async def get_rank_info(self, summoner_id: str) -> Optional[dict]:
        url = f"{self.summoner_base_url}/lol/league/v4/entries/by-summoner/{summoner_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    for entry in data:
                        if entry.get('queueType') == 'RANKED_SOLO_5x5':
                            return entry
                    return None
                else:
                    print(f"Erreur Rank API : status {response.status} url {url}")
                    print(await response.text())
                    return None



    def create_player_embed(self,summoner_data: dict, rank_data: dict, riot_id: str) -> discord.Embed:
        # Toujours afficher le Riot ID
        embed = discord.Embed(
            title=f"🔍 Profil de {riot_id}",
            color=0x00ff00
        )
        # On affiche le niveau si dispo, sinon “Inconnu”
        embed.add_field(
            name="👤 Informations générales",
            value=f"**Niveau:** {summoner_data.get('summonerLevel', 'Inconnu')}\n"
            f"**Riot ID:** {riot_id}",
            inline=False
        )
        # Le reste inchangé
        if rank_data:
            tier = rank_data.get('tier', 'UNRANKED')
            rank = rank_data.get('rank', '')
            lp = rank_data.get('leaguePoints', 0)
            wins = rank_data.get('wins', 0)
            losses = rank_data.get('losses', 0)
            if wins + losses > 0:
                winrate = round((wins / (wins + losses)) * 100, 1)
            else:
                winrate = 0
            rank_emoji = {
                    'IRON': '🤎', 'BRONZE': '🥉', 'SILVER': '🥈', 'GOLD': '🥇',
                    'PLATINUM': '💎', 'EMERALD': '<3', 'DIAMOND': '💎', 'MASTER': '👑',
                    'GRANDMASTER': '👑', 'CHALLENGER': '🏆'
            }.get(tier, '❓')
            embed.add_field(
                name="🏆 Rang Solo/Duo",
                value=f"{rank_emoji} **{tier.title()} {rank}** ({lp} LP)\n"
                     f"📊 **Winrate:** {winrate}% ({wins}W / {losses}L)",
                inline=False
            )
        else:
            embed.add_field(
                name="🏆 Rang Solo/Duo",
                value="❓ **Non classé**",
                inline=False
            )
        return embed



    @commands.command(name='lookup')
    async def lookup_player(self,ctx, *, riot_id: str):
        loading_msg = await ctx.send("🔍 Recherche en cours...")

        if "#" not in riot_id:
            await loading_msg.edit(content="❌ Format Riot ID invalide. Utilise : !lookup GameName#TagLine (ex: Zanshoes#EUW)")
            return

        game_name, tag_line = riot_id.split("#", 1)
        puuid = await self.get_puuid_by_riot_id(game_name, tag_line)
        if not puuid:
            await loading_msg.edit(content="❌ Joueur introuvable avec ce Riot ID !")
            return

        summoner_data = await self.get_summoner_by_puuid(puuid)
        if not summoner_data:
            await loading_msg.edit(content="❌ Impossible de récupérer les infos du joueur (Riot API).")
            return

        rank_data = await self.get_rank_info(summoner_data['id'])
        print("summoner_data reçu:", summoner_data)

        embed = self.create_player_embed(summoner_data, rank_data, riot_id=riot_id)
        await loading_msg.edit(content="", embed=embed)
    
    
    @commands.command(name='help_lol')
    async def help_command(self,ctx):
        embed = discord.Embed(
            title="🎮 Commandes du Bot League of Legends",
            description="**IMPORTANT** : Utilise le Riot ID sous la forme `GameName#TagLine` (ex: Zanshoes#EUW)",
            color=0x00ff00
        )
        embed.add_field(
            name="!lookup [GameName#TagLine]",
            value="Affiche les informations et le rang d'un joueur",
            inline=False
        )
        embed.add_field(
            name="!game [GameName#TagLine]",
            value="(Déprécié) Analyse la partie en cours d'un joueur",
            inline=False
        )
        embed.add_field(
            name="!help_lol",
            value="Affiche cette aide",
            inline=False
        )
        embed.add_field(
            name="!clown",
            value="Affiche à l'écran un jungler de la faille",
            inline=False
        )
        await ctx.send(embed=embed)
    
async def setup(bot):
  await bot.add_cog(RiotAPI(bot, RIOT_API_KEY))