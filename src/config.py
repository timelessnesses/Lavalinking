import discord
from discord.ext import commands
import sqlite3
class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group()
    async def config(self, ctx: commands.Context):
        """
        Configure the bot.
        """
        pass

    @config.command()
    async def default_lavalink(self, ctx: commands.Context, host: str="", port: int=8080, password: str = "youshallnotpass"):
        db = sqlite3.connect("database.sqlite3")
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO config(server_id, lavalink_host, lavalink_port, lavalink_password)
            VALUES(?, ?, ?, ?)
            """, (ctx.guild.id, host, port, password))
        db.commit()
        db.close()
        await ctx.reply(
            embed=discord.Embed(
                title="Success",
                description="Default lavalink server set.",
            )
        )
        