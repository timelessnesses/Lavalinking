import sqlite3

import discord
import wavelink
from discord.ext import commands


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group()
    async def config(self, ctx: commands.Context):
        """
        Configure the bot.
        """

    @config.command()
    async def default_lavalink(
        self,
        ctx: commands.Context,
        host: str = "lavalink.rukchadisa.live",
        port: int = 8080,
        password: str = "youshallnotpass",
    ):
        """
        Change the default lavalink host and port. (Specific to the guild)
        """
        await ctx.send(
            embed=discord.Embed(
                title="Testing connection to Lavalink",
                description="Please wait...",
                color=discord.Color.yellow(),
            )
        )
        node = await wavelink.NodePool.create_node(
            bot=self.bot, host=host, port=port, password=password
        )

        if node:
            if self.bot.Node.is_connected():
                await ctx.send(
                    embed=discord.Embed(
                        title="Success!",
                        description="Lavalink connection successful!",
                        color=discord.Color.green(),
                    )
                )
                await node.disconnect()
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="Error!",
                    description="Lavalink connection failed!",
                    color=discord.Color.red(),
                )
            )
            return

        db = sqlite3.connect("database.sqlite3")
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO config(server_id, lavalink_host, lavalink_port, lavalink_password)
            VALUES(?, ?, ?, ?)
            """,
            (ctx.guild.id, host, port, password),
        )
        db.commit()
        db.close()
