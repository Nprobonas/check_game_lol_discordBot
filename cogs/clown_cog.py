import discord
import os
from discord.ext import commands

class ClownCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='clown')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def clown(self, ctx):
        """Commande d'affichage d'un jungler de la faille"""
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "image", "clown.webp")
        texte_intro = "Red nose, big foot, yellow jacket.."
        with open(image_path, "rb") as f:
            file = discord.File(f, filename="clown.webp")
            await ctx.send(content=texte_intro, file=file)

    @clown.error
    async def clown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"🕒 Arrête de spam bâtard ! Attends {error.retry_after:.1f} secondes avant de réutiliser !clown.")

async def setup(bot):
  await bot.add_cog(ClownCog(bot))