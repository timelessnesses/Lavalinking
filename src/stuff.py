import platform
import sys
from datetime import datetime, timedelta

import discord
import psutil
from discord.ext import commands

from . import utils

sys.path.append("..")
import humanize
import wavelink
from wavelink.ext import spotify
from config import config


class Stuff(
    commands.Cog,
):
    """
    Miscellaneous commands and stuffs that don't fit anywhere else.
    """

    def __init__(self, bot):
        self.bot = bot

    @property
    def display_emoji(self):
        return "💭"

    @commands.hybrid_command(name="credits", aliases=["c"])
    async def credits(self, ctx):
        """
        Shows the credits.
        """
        embed = discord.Embed(
            title="Credits", description="Thanks to everyone who using this bot!"
        )

        embed.add_field(name="Creator", value="[Unpredictable#9443] ")
        embed.add_field(
            name="The bot is also open-source!",
            value="https://github.com/timelessnesses/music-lavalink-bot",
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ping", aliases=["p"])
    async def ping(self, ctx):
        """
        Pong!
        """
        embed = discord.Embed(
            title="Pong!",
            description=f"{round(self.bot.latency * 1000)} ms from API websocket",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="status")
    async def status(self, ctx):
        """
        Status of bot like uptime, memory usage, etc.
        """
        embed = discord.Embed(
            title="Status", description="Bot status", color=discord.Color.green()
        )
        embed.add_field(name="CPU", value=f"{psutil.cpu_percent()}%")
        embed.add_field(name="RAM", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(name="Disk", value=f"{psutil.disk_usage('/').percent}%")
        embed.add_field(
            name="Uptime",
            value=f"{utils.time.human_timedelta(datetime.utcnow(), source=self.bot.start_time)}",
        )
        embed.add_field(name="Python", value=f"{platform.python_version()}")
        embed.add_field(name="Discord.py", value=f"{discord.__version__}")
        embed.add_field(name="Bot version", value=f"{self.bot.version_}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="node_stats")
    async def node_stats(self, ctx):
        """
        Shows the lavalink stats.
        """
        client: wavelink.ext.spotify.SpotifyClient = None
        if config.spotify_client_id and config.spotify_client_secret:
            client = spotify.SpotifyClient(
                client_id=config.spotify_client_id,
                client_secret=config.spotify_client_secret,
            )
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=config.lavalink_host,
            port=int(config.lavalink_port),
            password=config.lavalink_password,
            spotify_client=client,
        )
        node = wavelink.NodePool.get_node()
        embed = discord.Embed(
            title=f"Node Status for {config.lavalink_host}",
        )
        embed.add_field(name="Connected", value=node.is_connected())
        embed.add_field(name="Connected to", value=config.lavalink_host)
        embed.add_field(name="Lavalink's Server CPU Cores", value=node.stats.cpu_cores)
        embed.add_field(
            name="Lavalink's Uptime",
            value=timedelta(milliseconds=round(node.stats.uptime, 2)),
        )
        embed.add_field(name="Lavalink's occupied players", value=node.stats.players)
        embed.add_field(
            name="Lavalink's playing players", value=node.stats.playing_players
        )
        embed.add_field(
            name="Lavalink's Memory Free",
            value=humanize.naturalsize(node.stats.memory_free, binary=True),
        )
        embed.add_field(
            name="Lavalink's Memory Used",
            value=humanize.naturalsize(node.stats.memory_used, binary=True),
        )
        embed.add_field(
            name="Lavalink's Server load",
            value=f"{round(node.stats.lavalink_load,3)* 100}%",
        )
        await ctx.send(embed=embed)
        await wavelink.NodePool.get_node().disconnect()


async def setup(bot):
    await bot.add_cog(Stuff(bot))
