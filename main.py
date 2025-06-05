import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
DISCORD_TOKEN= os.getenv('DISCORD_TOKEN')
RIOT_API_KEY= os.getenv('RIOT_API_KEY')

# Intents Discord
intents = discord.Intents.default()
intents.message_content = True

# Création du bot
bot = commands.Bot(command_prefix='!', intents=intents)

class RiotAPI:
    """Classe pour gérer les appels à l'API Riot Games"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://euw1.api.riotgames.com"
        self.headers = {"X-Riot-Token": api_key}

    async def get_summoner_by_name(self, summoner_name: str) -> Optional[dict]:
        """Récupère les infos d'un invocateur par son nom"""
        url = f"{self.base_url}/lol/summoner/v4/summoners/by-name/{summoner_name}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
                        print(f"Status {response.status}, URL: {url}")
                        print(await response.text())
            except Exception as e:
                print(f"Erreur API: {e}")
                return None
    
    async def get_rank_info(self, summoner_id: str) -> Optional[dict]:
        """Récupère les informations de rang d'un joueur"""
        url = f"{self.base_url}/lol/league/v4/entries/by-summoner/{summoner_id}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Cherche le rang en Solo/Duo
                        for entry in data:
                            if entry.get('queueType') == 'RANKED_SOLO_5x5':
                                return entry
                        return None
                    else:
                        return None
            except Exception as e:
                print(f"Erreur API: {e}")
                return None
    
    async def get_current_game(self, summoner_id: str) -> Optional[dict]:
        """Récupère la partie en cours d'un joueur"""
        url = f"{self.base_url}/lol/spectator/v4/active-games/by-summoner/{summoner_id}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
            except Exception as e:
                print(f"Erreur survenue : {e}")
                return None

# Instance de l'API Riot
riot_api = RiotAPI(RIOT_API_KEY)

def create_player_embed(summoner_data: dict, rank_data: dict) -> discord.Embed:
    """Crée un embed Discord pour afficher les infos d'un joueur"""
    
    embed = discord.Embed(
        title=f"🔍 Profil de {summoner_data['name']}",
        color=0x00ff00
    )
    
    # Informations de base
    embed.add_field(
        name="👤 Informations générales",
        value=f"**Niveau:** {summoner_data['summonerLevel']}\n"
              f"**Nom:** {summoner_data['name']}",
        inline=False
    )
    
    # Informations de rang
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
        
        # Émoji selon le rang
        rank_emoji = {
            'IRON': '🤎', 'BRONZE': '🥉', 'SILVER': '🥈', 'GOLD': '🥇',
            'PLATINUM': '💎', 'DIAMOND': '💎', 'MASTER': '👑',
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
    """Crée un embed pour afficher la partie en cours"""
    
    embed = discord.Embed(
        title="🎮 Partie en cours",
        description="Analyse des joueurs dans la partie",
        color=0x0099ff
    )
    
    # Séparer les équipes
    blue_team = []
    red_team = []
    
    for player in players_info:
        if player['teamId'] == 100:  # Équipe bleue
            blue_team.append(player)
        else:  # Équipe rouge
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
    
    # Ajouter les équipes
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

@bot.event
async def on_ready():
    print(f'{bot.user} la fine lame est connecté !')
    
# Démarrage du bot et load du token dans .env

token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("Token Discord non disponible ou déprécié")

# try:
#     await bot.start(token)
# except discord.errors.LoginFailure:
#     print("Echech de Connexion")
# except Exception as e:
#     print(f"Erreur survenue : {e}")

@bot.command(name='lookup')
async def lookup_player(ctx, *, summoner_name: str):
    """Commande pour rechercher un joueur"""
    
    # Message de chargement
    loading_msg = await ctx.send("🔍 Recherche en cours...")
    
    try:
        # Récupérer les infos du joueur
        summoner_data = await riot_api.get_summoner_by_name(summoner_name)
        
        if not summoner_data:
            await loading_msg.edit(content="❌ Joueur introuvable!")
            return
        
        # Récupérer le rang
        rank_data = await riot_api.get_rank_info(summoner_data['id'])
        
        # Créer et envoyer l'embed
        embed = create_player_embed(summoner_data, rank_data)
        await loading_msg.edit(content="", embed=embed)
        
    except Exception as e:
        await loading_msg.edit(content=f"❌ Erreur: {str(e)}")

@bot.command(name='game')
async def current_game(ctx, *, summoner_name: str):
    """Commande pour voir la partie en cours d'un joueur"""
    
    loading_msg = await ctx.send("🔍 Analyse de la partie en cours...")
    
    try:
        # Récupérer les infos du joueur
        summoner_data = await riot_api.get_summoner_by_name(summoner_name)
        
        if not summoner_data:
            await loading_msg.edit(content="❌ Joueur introuvable !")
            return
        
        # Récupérer la partie en cours
        game_data = await riot_api.get_current_game(summoner_data['id'])
        
        if not game_data:
            await loading_msg.edit(content="❌ Aucune partie en cours !")
            return
        
        # Récupérer les infos de tous les joueurs
        players_info = []
        for participant in game_data['participants']:
            player_data = await riot_api.get_summoner_by_name(participant['summonerName'])
            if player_data:
                rank_info = await riot_api.get_rank_info(player_data['id'])
                participant['rank_info'] = rank_info
            players_info.append(participant)
        
        # Créer et envoyer l'embed
        embed = create_game_embed(game_data, players_info)
        await loading_msg.edit(content="", embed=embed)
        
    except Exception as e:
        await loading_msg.edit(content=f"❌ Erreur: {str(e)}")

@bot.command(name='help_lol')
async def help_command(ctx):
    """Commande d'aide"""
    embed = discord.Embed(
        title="🎮 Commandes du Bot League of Legends",
        description="Voici les commandes disponibles:",
        color=0x00ff00
    )
    
    embed.add_field(
        name="!lookup [nom_joueur]",
        value="Affiche les informations et le rang d'un joueur",
        inline=False
    )
    
    embed.add_field(
        name="!game [nom_joueur]",
        value="Analyse la partie en cours d'un joueur",
        inline=False
    )
    
    embed.add_field(
        name="!help_lol",
        value="Affiche cette aide",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Lancement du bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)