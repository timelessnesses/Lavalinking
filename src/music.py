import asyncio
import enum
import sys
import typing
from datetime import timedelta

import async_timeout
import discord
import wavelink
from discord.ext import commands, tasks
from dotenv import load_dotenv
from wavelink.ext import spotify

sys.path.append("..")
from config import config

load_dotenv()


class Type_Loop(enum.Enum):
    """
    Enum for the loop type.
    """

    NONE = "NONE"
    SONG = "SONG"
    QUEUE = "QUEUE"


class Alternative_Context:
    pass


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.connect())
        self.bindings: typing.Dict[int, typing.List[typing.Dict]] = {}
        self.skip_votes: typing.Dict[int, typing.List[discord.Member]] = {}

    async def connect(self):
        await self.bot.wait_until_ready()
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

    def cog_unload(self):
        self.bot.loop.create_task(self.disconnect())

    async def disconnect(self):
        try:
            await wavelink.NodePool.get_node().disconnect()
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, player: wavelink.Player, track: wavelink.Track
    ):
        guild = self.bindings[player.guild.id]
        count = 0
        for binding in guild:
            if binding["track"].id == track.id:
                binding.copy()
                channel = binding["channel"]
                ctx = Alternative_Context()
                ctx.send = channel.send
                ctx.guild = channel.guild
                ctx.author = binding["requester"]
                msg = await channel.send(
                    embed=await self.info(track, ctx, binding["vc"])
                )
                self.loop_time_update.start(track, msg, ctx, binding["vc"])
                binding["msg"] = msg

                while not binding["vc"].position in [0, track.duration]:
                    await asyncio.sleep(1)
                self.loop_time_update.cancel()
                break
            count += 1
        if player.loop != Type_Loop.NONE:
            self.bindings[player.guild.id].pop(count)
        self.bindings[player.guild.id].append(binding)

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: wavelink.Player, track: wavelink.Track, reason: str
    ):
        guild = self.bindings[player.guild.id]
        for binding in guild:
            if binding["track"].id == track.id:
                break
        msg = binding["msg"]
        await msg.channel.send(
            embed=discord.Embed(
                title="Track ended", description=f"Server Reason: {reason}"
            )
        )
        await msg.delete()

        try:
            loop = player.loop
        except AttributeError:
            loop = Type_Loop.NONE
            player.loop = loop
        if loop != Type_Loop.NONE:
            if loop == Type_Loop.SONG:
                await player.play(track)
            elif loop == Type_Loop.QUEUE:
                pass
            else:
                del self.bindings[player.guild.id][
                    self.bindings[player.guild.id].index(binding)
                ]

        else:
            next_ = await player.queue.get_wait()
            if next_:
                await player.play(next_)

    @tasks.loop(seconds=1)
    async def loop_time_update(
        self,
        track: wavelink.Track,
        msg: discord.Message,
        ctx: commands.Context,
        vc: wavelink.Player,
    ):
        try:
            await msg.edit(embed=await self.info(track, ctx, vc))
        except AttributeError:
            pass

    async def cog_before_invoke(self, ctx: commands.Context):
        await ctx.defer()
        if not ctx.guild:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="This command can only be used in a server.",
                    color=discord.Color.red(),
                )
            )
            raise commands.CommandError("This command can only be used in a server.")
        if not ctx.author.voice:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel to use this command.",
                    color=discord.Color.red(),
                )
            )
            raise commands.CommandError(
                "You must be in a voice channel to use this command."
            )
        if (
            not ctx.voice_client
            and not ctx.invoked_with in ["play", "join", ""]
            and ctx.invoked_with in [str(command) for command in self.music.commands]
        ):
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I am not in a voice channel.",
                    color=discord.Color.red(),
                )
            )
            raise commands.CommandError("I am not in a voice channel.")

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
        if ctx.author.voice.channel and not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(
                cls=wavelink.Player
            )
        else:
            if ctx.voice_client:
                vc: wavelink.Player = ctx.voice_client
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="You must be in a voice channel to use this command.",
                        color=discord.Color.red(),
                    )
                )
        try:
            track = (
                await wavelink.YouTubeTrack.search(query)
                if not "list=" in query
                else await wavelink.NodePool.get_node().get_playlist(
                    wavelink.YouTubePlaylist, query
                )
            )
        except wavelink.errors.LoadTrackError:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Could not load track.",
                    color=discord.Color.red(),
                )
            )
        except wavelink.errors.LavalinkException:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Lavalink server error.",
                    color=discord.Color.red(),
                )
            )
        if not track:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Could not find a track with that name. ",
                    color=discord.Color.red(),
                )
            )
        if isinstance(track, (tuple, list)) and "list=" in query:
            for track_ in track:
                try:
                    self.bindings[ctx.guild.id].append(
                        {
                            "track": track_,
                            "vc": vc,
                            "requester": ctx.author,
                            "channel": await ctx.guild.fetch_channel(ctx.channel.id),
                        }
                    )
                except (KeyError, AttributeError):
                    self.bindings[ctx.guild.id] = [
                        {
                            "track": track,
                            "vc": ctx.voice_client,
                            "requester": ctx.author,
                            "channel": await ctx.guild.fetch_channel(ctx.channel.id),
                        }
                    ]
                await ctx.send(
                    embed=(
                        discord.Embed(
                            title=f"Added {track_.title} to the queue",
                            color=discord.Color.green(),
                        )
                    )
                )
                await vc.play(track[0]) if not vc.is_playing() else vc.queue.put_wait(
                    track_
                )
        else:
            try:
                self.bindings[ctx.guild.id].append(
                    {
                        "track": track[0],
                        "vc": vc,
                        "requester": ctx.author,
                        "channel": await ctx.guild.fetch_channel(ctx.channel.id),
                    }
                )
            except (KeyError, AttributeError):
                self.bindings[ctx.guild.id] = [
                    {
                        "track": track[0],
                        "vc": ctx.voice_client,
                        "requester": ctx.author,
                        "channel": await ctx.guild.fetch_channel(ctx.channel.id),
                    }
                ]

            await vc.play(track[0]) if not vc.is_playing() else await vc.queue.put_wait(
                track[0]
            )
            await ctx.send(
                embed=discord.Embed(
                    title=f"Added {track[0].title} to the queue",
                    color=discord.Color.green(),
                )
            )

    @music.command()
    async def pause(self, ctx: commands.Context):
        """
        Pause the music
        """
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
        [await vc.pause() if not vc.is_paused() else await vc.resume()]
        await ctx.send(
            embed=discord.Embed(
                title=f"{'Paused' if vc.is_paused() else 'Resumed'}",
                description=f"{'Paused' if vc.is_paused() else 'Resumed'} your song.",
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def stop(self, ctx: commands.Context):
        """
        Stop the music
        """
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
        vc.queue.reset()
        await ctx.send(
            embed=discord.Embed(
                title="Stopped",
                description="Stopped your song and also cleared the queue.",
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def loop(self, ctx: commands.Context, type: Type_Loop):
        """
        Loop the current song or entire queue (under development)
        """

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
            try:
                vc.loop = (
                    Type_Loop.SONG if not vc.loop == Type_Loop.SONG else Type_Loop.NONE
                )
            except AttributeError:
                vc.loop = Type_Loop.SONG
            await ctx.send(
                embed=discord.Embed(
                    title=f"{'Turned on' if vc.loop == Type_Loop.SONG else 'Turned off'} loop",
                    description=f"{'Turned on' if vc.loop == Type_Loop.SONG else 'Turned off'} loop for your song.",
                )
            )
        elif type == Type_Loop.QUEUE:
            try:
                vc.loop = (
                    Type_Loop.QUEUE
                    if not vc.loop == Type_Loop.QUEUE
                    else Type_Loop.NONE
                )
            except AttributeError:
                vc.loop = Type_Loop.QUEUE
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Looping the queue is not supported yet.",
                )
            )

    @music.command()
    async def volume(self, ctx: commands.Context, volume: int = None):
        """
        Change the volume of the music (0-500)
        """
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
        if volume is None:
            return await ctx.send(
                embed=discord.Embed(
                    title="Volume",
                    description=f"The volume is currently set to {vc.volume}.",
                    color=discord.Color.green(),
                )
            )
        if volume not in range(0, 500):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="The volume must be between 0 and 1000.",
                    color=discord.Color.red(),
                )
            )
        await vc.set_volume(volume / 100)
        await ctx.send(
            embed=discord.Embed(
                title="Volume",
                description=f"The volume has been set to {vc.volume}.",
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def skip(self, ctx: commands.Context):
        """
        Skip the current song
        """
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
        if vc.is_paused():
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="The player is currently paused.",
                    color=discord.Color.red(),
                )
            )
        requester = None
        for x in self.bindings[ctx.guild.id]:
            if x["track"].id == vc.track.id:
                requester = x["requester"]
            break
        if requester is None:
            requester = "Unknown"
        if not requester.id != ctx.author.id:
            try:
                async with async_timeout.timeout(2):
                    next_ = await vc.queue.get_wait()
            except asyncio.TimeoutError:
                await ctx.send(
                    embed=discord.Embed(
                        title="Warning",
                        description="There are no songs in the queue.",
                        color=discord.Color.yellow(),
                    )
                )
                await vc.stop()
                return
            if not next_:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="There is no song currently playing.",
                        color=discord.Color.red(),
                    )
                )
            await vc.play(next_)
            await ctx.send(
                embed=discord.Embed(
                    title="Skipped",
                    description="Skipped your song.",
                    color=discord.Color.green(),
                )
            )
        else:
            if not self.skip_votes.get(ctx.guild.id):
                self.skip_votes[ctx.guild.id] = []
            if ctx.author.id in self.skip_votes[ctx.guild.id]:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="You have already voted to skip this song.",
                        color=discord.Color.red(),
                    )
                )
            if len(self.skip_votes[ctx.guild.id]) >= 2:
                next_ = vc.queue.get_wait()
                if not next_:
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Error",
                            description="There is no song currently playing.",
                            color=discord.Color.red(),
                        )
                    )
                await vc.play(next_)
                await ctx.send(
                    embed=discord.Embed(
                        title="Skipped",
                        description="Skipped your song.",
                        color=discord.Color.green(),
                    )
                )
            else:
                self.skip_votes[ctx.guild.id].append(ctx.author.id)

    @music.command()
    async def now(self, ctx: commands.Context):
        """
        Get the current song
        """
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
        await ctx.send(embed=await self.info(vc.track, ctx, vc))

    @music.command()
    async def queue(self, ctx: commands.Context):
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
        queue = [x.title for x in vc.queue]
        if not queue:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently in the queue.",
                    color=discord.Color.red(),
                )
            )
        count = 1
        embed = discord.Embed(
            title="Queue",
            description="There's currently {} songs in the queue.\nLimiting 50 queues".format(
                len(vc.queue)
            ),
            color=discord.Color.green(),
        )
        for x in queue[:50]:
            embed.add_field(name=f"{count}", value=f"{x}")
            count += 1
        await ctx.send(embed=embed)

    async def info(
        self, current_music: wavelink.Track, ctx: commands.Context, vc: wavelink.Player
    ):
        try:
            thumbnail = current_music.thumbnail
        except AttributeError:
            try:
                thumbnail = current_music.thumb
            except AttributeError:
                thumbnail = None
        return (
            discord.Embed(
                title="Now Playing",
                description="Now playing: {}".format(current_music.title),
                color=discord.Color.green(),
            )
            .set_thumbnail(url=thumbnail)
            .set_footer(
                text="Requested by: {}\nThumbnail could be not accurate.".format(
                    ctx.author
                )
            )
            .add_field(
                name="Duration",
                value=str(timedelta(seconds=current_music.duration)),
                inline=True,
            )
            .add_field(
                name="Currently at",
                value=str(timedelta(seconds=vc.position)),
                inline=True,
            )
            .add_field(
                name="Listen at",
                value=vc.channel.mention,
            )
            .add_field(name="Author", value=current_music.author, inline=True)
            .add_field(name="URL", value=current_music.uri, inline=True)
        )


async def setup(bot):
    await bot.add_cog(Music(bot))
