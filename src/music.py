import logging
import typing
import regex

import discord
import wavelink
import wavelink.ext.spotify
from discord.ext import commands

from config import config

from .utils.types import Sources


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
            color=discord.Color.red(), title="Error", description=title
        )

    async def cog_check(self, ctx: commands.Context) -> bool:  # type: ignore
        if ctx.guild is None:
            return False

    @commands.hybrid_command()  # type: ignore
    async def join(
        self,
        ctx: commands.Context,
        channel: typing.Optional[
            typing.Union[discord.VoiceChannel, discord.StageChannel]
        ] = None,
    ) -> typing.Optional[wavelink.Player]:
        try:
            channel = channel or ctx.author.voice.channel  # type: ignore[union-attr]
        except AttributeError:
            await ctx.reply(embed=self.generate_error("Voice chat argument required."))
            return None

        vc = await channel.connect(cls=wavelink.Player)  # type: ignore[union-attr]
        return vc

    async def get_vc(self, ctx: commands.Context) -> wavelink.Player:
        vc: typing.Optional[wavelink.Player] = None

        if ctx.voice_client:
            vc: wavelink.Player = ctx.voice_client
        elif wavelink.NodePool.get_connected_node().get_player(ctx.guild.id): # type: ignore[union-attr]
            vc: wavelink.Player = wavelink.NodePool.get_connected_node().get_player(
                ctx.guild.id # type: ignore[union-attr]
            )
        else:
            vc: wavelink.Player = await self.join(ctx)

        return vc

    @commands.hybrid_command()  # type: ignore
    async def play(
        self, ctx: commands.Context, query: str, source: Sources = "YouTube"
    ) -> None:
        vc = await self.get_vc(ctx)
        

    @commands.hybrid_command()  # type: ignore
    async def volume(
        self, ctx: commands.Context, volume: discord.app_commands.Range[int, 0, 1000]
    ) -> None:
        vc = await self.get_vc(ctx)
        await vc.set_volume(volume)
        await ctx.reply(
            embed=discord.Embed(
                title="Success",
                description="Successfully set volume to: {}".format(volume),
                color=discord.Color.green(),
            )
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
