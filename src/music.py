import wavelink
from wavelink.ext import spotify
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
from datetime import timedelta
import sys

sys.path.append("..")
from config import config

load_dotenv()
import os


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.connect())

    async def connect(self):
        await self.bot.wait_until_ready()
        client: wavelink.ext.spotify.SpotifyClient = None
        if os.getenv("MUSIC_SPOTIFY_CLIENT_ID") and os.getenv(
            "MUSIC_SPOTIFY_CLIENT_SECRET"
        ):
            client = spotify.SpotifyClient(
                client_id=os.getenv("MUSIC_SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("MUSIC_SPOTIFY_CLIENT_SECRET"),
            )
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=os.getenv("MUSIC_LAVALINK_HOST"),
            port=int(os.getenv("MUSIC_LAVALINK_PORT")),
            password=os.getenv("MUSIC_LAVALINK_PASSWORD"),
            spotify_client=client,
        )

    def cog_unload(self):
        self.bot.loop.create_task(self.disconnect())

    async def disconnect(self):
        await wavelink.NodePool.get_node().disconnect()

    async def cog_before_invoke(self, ctx: commands.Context):
        if not ctx.guild:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="This command can only be used in a server.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.author.voice:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel to use this command.",
                    color=discord.Color.red(),
                )
            )

    @commands.hybrid_group()
    async def music(self, ctx: commands.Context):
        """
        Music group commands
        """
        pass

    @music.command()
    async def join(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ):
        """
        Join a voice channel
        """
        if not channel:
            channel = ctx.author.voice.channel
        await ctx.send(
            embed=discord.Embed(
                title="Joining",
                description="Joining {}".format(channel.mention),
                color=discord.Color.yellow(),
            )
        )
        await channel.connect(cls=wavelink.Player)
        await ctx.send(
            embed=discord.Embed(
                title="Joined",
                description="Joined {}".format(channel.mention),
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def leave(self, ctx: commands.Context):
        """
        Leave the voice channel
        """
        await ctx.send(
            embed=discord.Embed(
                title="Leaving",
                description="Leaving {}".format(ctx.guild.me.voice.channel.mention),
                color=discord.Color.yellow(),
            )
        )
        await ctx.voice_client.disconnect()
        await ctx.send(
            embed=discord.Embed(
                title="Left",
                description="Left {}".format(ctx.guild.me.voice.channel.mention),
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def play_youtube(
        self, ctx: commands.Context, *, query: wavelink.YouTubeTrack
    ):
        """
        Play a song
        """
        if not ctx.voice_client:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            player = ctx.voice_client
        await ctx.send(
            embed=discord.Embed(
                title="Fetching",
                description="Fetching data with query: {}".format(query),
                color=discord.Color.yellow(),
            )
        )
        current_music = await player.play(query, replace=False)
        await ctx.send(
            embed=self.info(current_music, ctx, ctx.author.voice.channel.mention)
        )

    @music.command()
    async def play_spotify(self, ctx: commands.Context, *, query: spotify.SpotifyTrack):
        """
        Play a song
        """
        if not ctx.voice_client:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            player = ctx.voice_client
        await ctx.send(
            embed=discord.Embed(
                title="Fetching",
                description="Fetching data with query: {}".format(query),
                color=discord.Color.yellow(),
            )
        )
        current_music = await player.play(query, replace=False)
        await ctx.send(
            embed=self.info(current_music, ctx, ctx.author.voice.channel.mention)
        )

    def info(self, current_music: wavelink.Track, ctx: commands.Context, vc: str):
        return (
            discord.Embed(
                title="Now Playing",
                description="Now playing: {}".format(current_music.title),
                color=discord.Color.green(),
            )
            .set_thumbnail(url=current_music.thumbnail)
            .set_footer(text="Requested by: {}".format(ctx.author))
            .add_field(
                name="Duration",
                value=str(timedelta(seconds=current_music.duration)),
                inline=True,
            )
            .add_field(name="Author", value=current_music.author, inline=True)
            .add_field(name="URL", value=current_music.uri, inline=True)
        )


async def setup(bot):
    await bot.add_cog(Music(bot))
