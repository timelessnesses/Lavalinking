import sys
import typing
from datetime import timedelta

import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv
from wavelink.ext import spotify

sys.path.append("..")
from config import config

load_dotenv()
import os


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.connect())
        self.bindings: typing.Dict[
            int,
            typing.List[typing.Dict],
        ] = {}

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
                channel = await self.bot.fetch_channel(binding["channel"])
                if channel:
                    await channel.send(
                        embed=self.info(track, channel, binding["vc"].channel.mention)
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
    async def play(self, ctx: commands.Context, query: str):
        """
        Play a song
        """
        if not ctx.voice_client:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc = ctx.voice_client
        track = await vc.node.get_tracks(query=url, cls=wavelink.Track)
        if not track:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Could not find a track with that name.",
                    color=discord.Color.red(),
                )
            )
        await vc.play(track[0]) if not vc.is_playing() else vc.queue.put_wait(track[0])
        await ctx.send(
            embed=(
                discord.Embed(
                    title=f"Added {track[0].title} to the queue",
                    color=discord.Color.green(),
                )
            )
        )
        try:
            self.bindings[ctx.guild.id].append(
                {
                    "track": track[0],
                    "vc": vc,
                    "requester": ctx.author,
                    "channel": ctx.channel,
                }
            )
        except (KeyError, AttributeError):
            self.bindings[ctx.guild.id] = [
                {
                    "track": track[0],
                    "vc": ctx.voice_client,
                    "requester": ctx.author,
                    "channel": ctx.channel,
                }
            ]

    @music.command()
    async def pause(self, ctx: commands.Context):
        if not ctx.voice_client:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing:
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
        if not ctx.voice_client:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing:
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
