import requests
import discord
from dotenv import load_dotenv
from discord.ext import commands



class PromoGame(commands.Cog):
   
   
    def __init__(self, bot):
       self.bot = bot
    
    url = "https://api.isthereanydeal.com/v01/deals/list/"

    params = {
        "key" : API_KEY,
        "région" : "fr",
        "country" : "FR",
        "shops" : "steam,epic,gog,ubisoft,origin,rockstar",
        "limit" : 10,
        "price_cut" : 50,
    }

    response = requests.get(url, params=params)
    data = response.json()

    for deal in data["list"]:
        title = deal["title"]
        price_old = deal["price_old"]
        price_new = deal["price_new"]
        shop = deal["shop"]["name"]
        url_game = deal["urls"]["game"]
        end = deal.get("price_cut_end")
        print(f"{title} ({shop}) : {price_old}€ -> {price_new}€ {'jusqu’au ' + str(end) if end else ''} \n{url_game}\n")
        
        
async def setup(bot):
  await bot.add_cog(PromoGame(bot))