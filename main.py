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
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

# Intents Discord
intents = discord.Intents.default()
intents.message_content = True

# Création du bot
bot = commands.Bot(command_prefix='!', intents=intents)



class RiotAPI:
    def __init__(self, api_key: str):
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

    async def get_current_game(self, summoner_id: str) -> Optional[dict]:
        url = f"{self.summoner_base_url}/lol/spectator/v4/active-games/by-summoner/{summoner_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 403:
                    print("La commande !game est bloquée par RIOT sauf pour les comptes partners...")
                    return {"error":"Accès interdit"}
                else:
                    print(f"Erreur Spectator API : status {response.status} url {url}")
                    print(await response.text())
                    return None
                

riot_api = RiotAPI(RIOT_API_KEY)

def create_player_embed(summoner_data: dict, rank_data: dict, riot_id: str) -> discord.Embed:
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


def create_game_embed(game_data: dict, players_info: list) -> discord.Embed:
    embed = discord.Embed(
        title="🎮 Partie en cours",
        description="Analyse des joueurs dans la partie",
        color=0x0099ff
    )
    blue_team = []
    red_team = []
    for player in players_info:
        if player['teamId'] == 100:
            blue_team.append(player)
        else:
            red_team.append(player)
    def format_team(team_players, team_name, emoji):
        team_text = f"{emoji} **{team_name}**\n"
        for player in team_players:
            rank_info = player.get('rank_info', {})
            if rank_info:
                tier = rank_info.get('tier', 'UNRANKED')
                rank = rank_info.get('rank', '')
                lp = rank_info.get('leaguePoints', 0)
                rank_emoji = {
                    'IRON': '🤎', 'BRONZE': '🥉', 'SILVER': '🥈', 'GOLD': '🥇',
                    'PLATINUM': '💎', 'DIAMOND': '💎', 'MASTER': '👑',
                    'GRANDMASTER': '👑', 'CHALLENGER': '🏆'
                }.get(tier, '❓')
                team_text += f"{rank_emoji} {player['summonerName']} - {tier.title()} {rank} ({lp} LP)\n"
            else:
                team_text += f"❓ {player['summonerName']} - Non classé\n"
        return team_text
    if blue_team:
        embed.add_field(
            name="🔵 Équipe Bleue",
            value=format_team(blue_team, "BLUE", "🔵"),
            inline=True
        )
    if red_team:
        embed.add_field(
            name="🔴 Équipe Rouge",
            value=format_team(red_team, "RED", "🔴"),
            inline=True
        )
    return embed

# Event du démarrage du bot
@bot.event
async def on_ready():
    print(f'{bot.user} la fine lame est connecté !')

@bot.command(name='lookup')
async def lookup_player(ctx, *, riot_id: str):
    loading_msg = await ctx.send("🔍 Recherche en cours...")

    if "#" not in riot_id:
        await loading_msg.edit(content="❌ Format Riot ID invalide. Utilise : !lookup GameName#TagLine (ex: Zanshoes#EUW)")
        return

    game_name, tag_line = riot_id.split("#", 1)
    puuid = await riot_api.get_puuid_by_riot_id(game_name, tag_line)
    if not puuid:
        await loading_msg.edit(content="❌ Joueur introuvable avec ce Riot ID !")
        return

    summoner_data = await riot_api.get_summoner_by_puuid(puuid)
    if not summoner_data:
        await loading_msg.edit(content="❌ Impossible de récupérer les infos du joueur (Riot API).")
        return

    rank_data = await riot_api.get_rank_info(summoner_data['id'])
    print("summoner_data reçu:", summoner_data)

    embed = create_player_embed(summoner_data, rank_data, riot_id=riot_id)
    await loading_msg.edit(content="", embed=embed)

@bot.command(name='game')
async def current_game(ctx, *, riot_id: str):
    loading_msg = await ctx.send("🔍 Analyse de la partie en cours...")

    if "#" not in riot_id:
        await loading_msg.edit(content="❌ Format Riot ID invalide. Utilise : !game GameName#TagLine (ex: Zanshoes#EUW)")
        return

    game_name, tag_line = riot_id.split("#", 1)
    puuid = await riot_api.get_puuid_by_riot_id(game_name, tag_line)
    if not puuid:
        await loading_msg.edit(content="❌ Joueur introuvable avec ce Riot ID !")
        return

    summoner_data = await riot_api.get_summoner_by_puuid(puuid)
    if not summoner_data:
        await loading_msg.edit(content="❌ Impossible de récupérer les infos du joueur (Riot API).")
        return

    game_data = await riot_api.get_current_game(summoner_data['id'])
    if not game_data:
        await loading_msg.edit(content="❌ La commande !game est bloquée par RIOT sauf pour les comptes partenaires...")
        return

    players_info = []
    for participant in game_data['participants']:
        player_data = await riot_api.get_summoner_by_puuid(participant['puuid'])
        if player_data:
            rank_info = await riot_api.get_rank_info(player_data['id'])
            participant['rank_info'] = rank_info
        players_info.append(participant)

    embed = create_game_embed(game_data, players_info)
    await loading_msg.edit(content="", embed=embed)

@bot.command(name='help_lol')
async def help_command(ctx):
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
    
    
@bot.command(name='help_price')
async def help_price(ctx):
    embed = discord.Embed(
        title="Commandes du watcher prix cryptos",
        description="**IMPORTANT** :  Utilise !price [nom_crypto] afin d'afficher le prix et le sentiment du marché",
        color=0x00ff00
    )
    embed.add_field(
        name="!price [SOL]",
        value="Affiche les informations et le sentiment du marché sur un symbol crypto",
        inline=False
    )
    await ctx.send(embed=embed)
    

async def main():
    #Endroit pour charger les Cogs Discord
    await bot.load_extension("cogs.clown_cog")
    await bot.load_extension("cogs.price_watcher_cog")
    print("Cogs chargés avec succès !")
    # Start du bot via le token Discord
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Déconnexion \nKrabinoche retourne dans les abysses..")