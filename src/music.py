# mypy: disable-error-code="union-attr"

import logging
import typing

import discord
from discord.ext.commands.context import Context
import wavelink
import wavelink.ext.spotify
from discord.ext import commands

from config import config


class Music(commands.Cog):
    node: wavelink.Node
    sc: wavelink.ext.spotify.SpotifyClient
    bot: commands.Bot
    logger: logging.Logger
    connected: bool

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger("lavalinking.src.music")
        self.bot.loop.create_task(self.connect())
        self.connected = False

    async def connect(self) -> None:
        if self.connected:
            self.logger.warning("Already connected.")
            return
        await self.bot.wait_until_ready()
        self.node = wavelink.Node(
            uri=f"{'https' if config.lavalink_is_https else 'http'}://{config.lavalink_host}:{config.lavalink_port}",
            password=config.lavalink_password,
        )
        self.sc = wavelink.ext.spotify.SpotifyClient(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret,
        )
        await wavelink.NodePool.connect(
            client=self.bot, nodes=[self.node], spotify=self.sc
        )
        self.connected = True
        self.logger.info("Connected to Lavalink server.")

    async def cog_unload(self) -> None:
        self.logger.info(
            "Unloaded. (Automatically disconnecting from node by wavelink.)"
        )
    
    def generate_error(self, title: str) -> discord.Embed:
        return discord.Embed(
            color=discord.Color.red(),
            title="Error", 
            description=title
        )

    async def cog_check(self, ctx: commands.Context) -> bool: # type: ignore
        if ctx.guild is None:
            return False
        

    @commands.hybrid_command() # type: ignore
    async def join(
        self,
        ctx: commands.Context,
        channel: typing.Optional[
            typing.Union[
                discord.VoiceChannel,
                discord.StageChannel
            ]
        ] = None,
    ) -> None:
        
        try:
            channel = channel or ctx.author.voice.channel
        except AttributeError:
            await ctx.reply(embed=self.generate_error("Voice chat argument required."))
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
