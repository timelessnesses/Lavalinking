import sys
import typing
from datetime import timedelta
import enum

import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv
from wavelink.ext import spotify
import asyncio

sys.path.append("..")
from config import config

load_dotenv()
import os


class Type_Loop(enum.Enum):
    """
    Enum for the loop type.
    """

    NONE = 0
    SONG = 1
    QUEUE = 2


class Type_Query(enum.Enum):
    """
    Enum for the query type.
    """

    SPOTIFY = 0
    YOUTUBE = 1
    YOUTUBE_PLAYLIST = 2
    SPOTIFY_PLAYLIST = 3
    SOUNDCLOUD = 4


class Alternative_Context:
    pass

class Information_Bindings(typing.TypedDict):
    track: wavelink.Track
    channel: discord.TextChannel
    requester: typing.Union[discord.Member, discord.User]
    vc: typing.Union[discord.VoiceProtocol, wavelink.Player]

class Bindings(typing.TypedDict):
    guild_id: typing.List[Information_Bindings]

class Loop_Queue_Information(typing.TypedDict):
    queue: wavelink.Queue
    loop: Type_Loop
    info: Information_Bindings

class Loop_Queue(typing.TypedDict):
    guild_id: typing.List[Loop_Queue_Information]

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.connect())
        self.bindings: Bindings = {}
        self.loop_queue_list: Loop_Queue = {}
        self.loop_queue_list["guild_id"] = []
        self.bindings["guild_id"] = []

    async def connect(self):
        await self.bot.wait_until_ready()
        client: wavelink.ext.spotify.SpotifyClient = None
        if os.getenv("MUSIC_SPOTIFY_CLIENT_ID") and os.getenv(
            "MUSIC_SPOTIFY_CLIENT_SECRET"
        ):
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

    def cog_unload(self):
        self.bot.loop.create_task(self.disconnect())

    async def disconnect(self):
        await wavelink.NodePool.get_node().disconnect()

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, player: wavelink.Player, track: wavelink.Track
    ):

        guild = self.bindings[player.guild.id]
        for binding in guild:
            if binding["track"] == track:
                channel = binding["channel"]
                ctx = Alternative_Context()
                ctx.send = channel.send
                ctx.guild = channel.guild
                ctx.author = binding["requester"]
                if channel:
                    await channel.send(
                        embed=self.info(track, ctx, binding["vc"].channel.mention)
                    )

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
    async def play(
        self,
        ctx: commands.Context,
        *,
        query: str,
    ):

        """
        Play a song
        """
        if not ctx.author.voice.channel:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc = ctx.voice_client
        track = query
        if not track:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Could not find a track with that name. ",
                    color=discord.Color.red(),
                )
            )
        try:
            self.bindings[ctx.guild.id].append(
                {
                    "track": track,
                    "vc": vc,
                    "requester": ctx.author,
                    "channel": ctx.channel,
                }
            )
        except (KeyError, AttributeError):
            self.bindings[ctx.guild.id] = [
                {
                    "track": track,
                    "vc": ctx.voice_client,
                    "requester": ctx.author,
                    "channel": ctx.channel,
                }
            ]
        await vc.play(track) if not vc.is_playing() else vc.queue.put_wait(track)
        await ctx.send(
            embed=(
                discord.Embed(
                    title=f"Added {track.title} to the queue",
                    color=discord.Color.green(),
                )
            )
        )

    @music.command()
    async def pause(self, ctx: commands.Context):
        if not ctx.author.voice.channel:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing():
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently playing.",
                    color=discord.Color.red(),
                )
            )
        vc: wavelink.Player = ctx.voice_client
        [await vc.pause() if vc.is_paused() else await vc.resume()]
        await ctx.send(
            embed=discord.Embed(
                title=f"{'Paused' if vc.is_paused() else 'Resumed'}",
                description=f"{'Paused' if vc.is_paused() else 'Resumed'} your song.",
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def stop(self, ctx: commands.Context):
        if not ctx.author.voice.channel:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing():
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently playing.",
                    color=discord.Color.red(),
                )
            )
        vc: wavelink.Player = ctx.voice_client
        await vc.stop()
        await ctx.send(
            embed=discord.Embed(
                title="Stopped",
                description="Stopped your song.",
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def loop(self, ctx: commands.Context, type: Type_Loop):
        if not ctx.author.voice.channel:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing():
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently playing.",
                    color=discord.Color.red(),
                )
            )
        vc: wavelink.Player = ctx.voice_client
        if type == Type_Loop.SONG:
            setattr(vc, "loop", True if not getattr(vc, "loop") else False)
            await ctx.send(
                embed=discord.Embed(
                    title=f"{'Turned on' if getattr(vc, 'loop') else 'Turned off'} loop",
                    description=f"{'Turned on' if getattr(vc, 'loop') else 'Turned off'} loop for your song.",
                )
            )
        elif type == Type_Loop.QUEUE:
            

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
