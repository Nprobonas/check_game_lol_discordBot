import discord
from discord.ext import commands
import aiohttp
import asyncio
from typing import Optional, List, Dict, Tuple
from collections import defaultdict


# smurf_detector.py

class SmurfDetector:
    def __init__(self):
            pass

    def is_smurf(self, summoner_data, rank_data=None):
        niveau = summoner_data.get('summonerLevel', 0)
        winrate = None
        nb_games = None
        tier = None

        if rank_data:
            wins = rank_data.get('wins', 0)
            losses = rank_data.get('losses', 0)
            nb_games = wins + losses
            winrate = round((wins / nb_games) * 100, 1) if nb_games > 0 else 0
            tier = rank_data.get('tier', 'UNRANKED')
        else:
            wins = losses = 0

        # Détection simple
        if niveau < 30 and winrate > 65:
            # Cas d'un compte inférieur au lvl 30
            return True, f"Smurf probable -> Niveau inférieur à 30 mais winrate élevé ({winrate}%)."
        elif niveau < 50 and winrate is not None and winrate > 60 and nb_games is not None and nb_games > 20:
            return True, f"Niveau bas ({niveau}), winrate de ({winrate}%) en ranked pour ({nb_games} parties)."
        elif tier and tier in ['PLATINUM', 'EMERALD', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER'] and niveau < 60:
            return True, f"Rang élevé ({tier}) avec niveau bas ({niveau})."
      

        return False, None
