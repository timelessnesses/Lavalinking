import asyncio
import sys
import typing
from datetime import timedelta

import async_timeout
import discord
import wavelink
from discord.ext import commands, tasks
from discord.utils import get
from discord_together import DiscordTogether
from dotenv import load_dotenv

try:
    pass
except ImportError:
    pass

from wavelink.ext import spotify

from .utils.enums import Enum_Applications, Enum_Source, Type_Loop

sys.path.append("..")
import os

from config import config

load_dotenv()


class Alternative_Context:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        return self.__dict__.get(name)

    def __setattr__(self, name, value) -> None:
        self.__dict__[name] = value


# basic implementation of loop queue
class Loop_Queue:
    def __init__(self, *tracks: wavelink.Track):
        self.tracks = tracks
        self.current = 0
        print(
            "got initialized with" + "\n".join([str(track.title) for track in tracks])
        )

    def __iter__(self):
        return self.tracks.__iter__()

    def next(self):
        try:
            self.current += 1
            return self.tracks[self.current]
        except IndexError:
            self.current = 0
            return self.tracks[self.current]


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.connect())
        self.bindings: typing.Dict[int, typing.List[typing.Dict]] = {}
        self.skip_votes: typing.Dict[int, typing.List[discord.Member]] = {}
        self.now_playing: typing.Dict[int, typing.Dict] = {}
        self.now_playing2: typing.Dict[int, wavelink.Track] = {}
        self.playing: typing.Dict[
            int, bool
        ] = {}  # guild and their playing status since wavelink is so unstable

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
        self.client = client
        self.together = await DiscordTogether(config.token)

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
        self.playing[player.guild.id] = True
        print("Track started " + str(self.playing))
        guild = self.bindings[player.guild.id]
        count = 0
        for binding in guild:
            if binding["track"].id == track.id:
                channel = binding["channel"]
                ctx = Alternative_Context()
                ctx.send = channel.send
                ctx.guild = channel.guild
                ctx.author = binding["requester"]
                msg = await channel.send(
                    embed=await self.info(track, ctx, binding["vc"])
                )
                t = tasks.loop(seconds=5)(
                    self.loop_time_update
                )  # 5 seconds of not smashing discord api with requests :D
                t.start(track, msg, ctx, binding["vc"])
                binding["msg"] = msg
                self.now_playing[player.guild.id] = binding.copy()
                while not binding["vc"].position in [0, track.duration]:
                    await asyncio.sleep(1)
                t.cancel()
                break
            count += 1

        if player.loop != Type_Loop.NONE:
            try:
                self.bindings[player.guild.id].pop(count)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: wavelink.Player, track: wavelink.Track, reason: str
    ):
        self.playing[player.guild.id] = False
        print("Track ended " + str(self.playing))
        try:
            async with async_timeout.timeout(5):
                await player.queue.get_wait()
        except asyncio.TimeoutError:
            self.skip_votes[player.guild.id] = []
        try:
            binding = self.now_playing[player.guild.id]

            msg = binding["msg"]
            await msg.channel.send(
                embed=discord.Embed(
                    title="Track ended",
                    description=f"Server Reason: {reason}",
                ),
                delete_after=5,
            )
            await msg.delete()
        except Exception as e:
            print(e)

        try:
            loop = player.loop
        except AttributeError:
            loop = Type_Loop.NONE
            player.loop = loop
        if loop != Type_Loop.NONE:
            if loop == Type_Loop.SONG:
                await player.play(track)
            elif loop == Type_Loop.QUEUE:
                if (
                    reason == "FINISHED"
                ):  # ignore replace since skip command replace song
                    await player.play(self.queue_loop[player.guild.id].next())
            else:
                del self.bindings[player.guild.id][
                    self.bindings[player.guild.id].index(binding)
                ]

        else:
            next_ = await player.queue.get_wait()
            if next_:
                await player.play(next_)

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

    async def cog_check(self, ctx: commands.Context):
        await ctx.defer()
        if not ctx.guild:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="This command can only be used in a server.",
                    color=discord.Color.red(),
                )
            )
            return False
        elif int(os.getenv("DEBUG", 0)) and ctx.author.id not in self.owners:
            return False
        return True

    @commands.hybrid_group()
    async def music(self, ctx: commands.Context):
        """
        Music group commands
        """

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):  # wavelink doesn't disconnect automatically not pog champ
        if member.id == self.bot.user.id:
            if after.channel is None:
                vc: wavelink.Player = get(
                    self.bot.voice_clients, guild__id=member.guild.id
                )
                await vc.disconnect()

    @music.command()
    async def join(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ):
        """
        Join a voice channel
        """
        if not channel:
            channel = ctx.author.voice.channel
        if not channel:
            return await ctx.send(
                embed=discord.Embed(
                    title="No channel to join",
                    description="You need to be in a voice channel or specify one.",
                    color=discord.Color.red(),
                )
            )
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
        try:
            await ctx.voice_client.disconnect()
            await ctx.send(
                embed=discord.Embed(
                    title="Left",
                    description="Left {}".format(ctx.guild.me.voice.channel.mention),
                    color=discord.Color.green(),
                )
            )
        except:
            return await ctx.send(
                embed=discord.Embed(
                    title="Failed to disconnect", color=discord.Color.red()
                )
            )

    @music.command()
    async def play(
        self,
        ctx: commands.Context,
        query: str = None,
        source: Enum_Source = Enum_Source.YouTube,
    ):
        """
        Play a song if query is none then it will play the last song in the queue
        """
        if ctx.author.voice and not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(
                cls=wavelink.Player
            )
            await vc.set_volume(100)
        else:
            if ctx.voice_client:
                vc: wavelink.Player = ctx.voice_client
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="You must be in a voice channel and same channel as the bot to use this command.",
                        color=discord.Color.red(),
                    )
                )
        if not vc.__dict__.get("loop"):
            vc.loop = Type_Loop.NONE
        if not query:  # none
            # get last song in the queue
            try:
                async with async_timeout.timeout(1):
                    har = await vc.queue.get_wait()
                    return await vc.play(har)
            except asyncio.TimeoutError:
                await ctx.send(
                    embed=discord.Embed(
                        title="No song in queue",
                        description="There is no song in the queue after waited for 1 second",
                        color=discord.Color.red(),
                    )
                )
        try:
            track = None
            if ctx.message.attachments:
                track = []
                count = 1
                for attachment in ctx.message.attachments:
                    if (False):
                        await ctx.send(
                            embed=discord.Embed(
                                title="Error",
                                description=f"Attachment number {count} has wrong content type.\nSkipping",
                            )
                        )
                        continue
                    count += 1
                    track.append(
                        (
                            (await wavelink.NodePool.get_node().get_tracks(
                                wavelink.Track, attachment.url
                            ))[0]
                        )
                    )
            elif "youtube.com" in query and "watch" in query:  # youtube link
                track = (
                    await wavelink.NodePool.get_node().get_tracks(
                        wavelink.YouTubeTrack, query
                    )
                )[0]
            elif "spotify.com" in query and ("playlist" in query or "album" in query):
                track = await wavelink.NodePool.get_node().get_tracks(
                    query=query, cls=spotify.SpotifyTrack
                )
            elif "spotify.com" in query and (
                not "playlist" in query or not "album" in query
            ):
                track = (
                    await wavelink.NodePool.get_node().get_tracks(
                        query=query, cls=spotify.SpotifyTrack
                    )
                )[0]
            elif "youtube.com" in query and "list" in query:
                track = await wavelink.NodePool.get_node().get_tracks(
                    query, cls=wavelink.YouTubePlaylist
                )
            elif "soundcloud.com" in query and not "sets" in query:
                track = (
                    await wavelink.NodePool.get_node().get_tracks(
                        query=query, cls=wavelink.SoundCloudTrack
                    )
                )[0]
            elif "soundcloud.com" in query and "sets" in query:
                track = await wavelink.NodePool.get_node().get_tracks(
                    query=query, cls=wavelink.SoundCloudTrack
                )
            elif " " in query:
                track = []
                for a in query.split(" "):
                    track.append((await wavelink.NodePool.get_node().get_tracks(
                                wavelink.Track, a
                            ))[0])
            else:
                if source == Enum_Source.YouTube:
                    track = await wavelink.YouTubeTrack.search(query, return_first=True)
                elif source == Enum_Source.SoundCloud:
                    track = (await wavelink.SoundCloudTrack.search(query))[0]
                elif source == Enum_Source.Spotify:
                    track = await spotify.SpotifyTrack.search(query, return_first=True)
                elif source == Enum_Source.SpotifyPlaylist:
                    track = await spotify.SpotifyTrack.search(query)
                elif source == Enum_Source.YouTubePlaylist:
                    track = await wavelink.YouTubeTrack.search(query)

        except wavelink.errors.LavalinkException as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"Lavalink server error.\n```py\nLavalinkException: {str(e)}\n```",
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
        if isinstance(track, (tuple, list)):
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
                    ),
                    delete_after=2,
                )

                await vc.play(track[0]) if not vc.is_playing() or not self.playing.get(
                    ctx.guild.id, False
                ) else await vc.queue.put_wait(track_)
        else:
            try:
                self.bindings[ctx.guild.id].append(
                    {
                        "track": track,
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

            await vc.play(track) if not vc.is_playing() or not self.playing.get(
                ctx.guild.id, False
            ) else await vc.queue.put_wait(track)
            await ctx.send(
                embed=discord.Embed(
                    title=f"Added {track.title} to the queue",
                    color=discord.Color.green(),
                )
            )

    @music.command()
    async def pause(self, ctx: commands.Context):
        """
        Pause the music
        """
        if (
            not ctx.author.voice
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )
        if self.playing.get(ctx.guild.id, False):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently playing.",
                    color=discord.Color.red(),
                )
            )
        vc: wavelink.Player = ctx.voice_client
        await vc.pause() if not vc.is_paused() else await vc.resume()
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
        if (
            not ctx.author.voice
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing() and not self.playing.get(
            ctx.guild.id, False
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently playing.",
                    color=discord.Color.red(),
                )
            )
        vc: wavelink.Player = ctx.voice_client
        vc.loop = Type_Loop.NONE
        await vc.stop()
        vc.queue.reset()
        del self.bindings[ctx.guild.id]
        del self.playing[ctx.guild.id]
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

        if (
            not ctx.author.voice
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing() and not self.playing.get(
            ctx.guild.id, False
        ):
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
                self.queue_loop[ctx.guild.id] = Loop_Queue(
                    self.now_playing[ctx.guild.id]["track"],
                    *[track for track in vc.queue],
                )
                print([track for track in vc.queue])
            except AttributeError:
                vc.loop = Type_Loop.QUEUE
                # copy all queues and current playing track to a new queue
                self.queue_loop[ctx.guild.id] = Loop_Queue(
                    self.now_playing[ctx.guild.id]["track"],
                    *[track for track in vc.queue],
                )
                print([track for track in vc.queue])
            await ctx.send(
                embed=discord.Embed(
                    title=f"{'Turned on' if vc.loop == Type_Loop.QUEUE else 'Turned off'} loop",
                    description=f"{'Turned on' if vc.loop == Type_Loop.QUEUE else 'Turned off'} loop for your queue.",
                    color=discord.Color.green(),
                )
            )
        elif type == Type_Loop.NONE:
            vc.loop = Type_Loop.NONE
            await ctx.send(
                embed=discord.Embed(
                    title="Turned off loop",
                    description="Turned off loop for your song.",
                )
            )
            return
        else:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Invalid loop type.",
                )
            )

    @music.command()
    async def volume(self, ctx: commands.Context, volume: int = None):
        """
        Change the volume of the music (0-500)
        """
        if (
            not ctx.author.voice
            or not ctx.voice_client
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )

        if not ctx.voice_client.is_playing() and not self.playing.get(
            ctx.guild.id, False
        ):
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
                    description=f"The volume is currently set to {int(vc.volume)}%.",
                    color=discord.Color.green(),
                )
            )
        if volume not in range(0, 500):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="The volume must be between 0 and 500.",
                    color=discord.Color.red(),
                )
            )
        await vc.set_volume(volume)
        await ctx.send(
            embed=discord.Embed(
                title="Volume",
                description=f"The volume has been set to {int(vc.volume)}.",
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def skip(self, ctx: commands.Context):
        """
        Skip the current song
        """
        if (
            not ctx.author.voice
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing() and not self.playing.get(
            ctx.guild.id, False
        ):
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
        requester = Alternative_Context()
        for x in self.bindings[ctx.guild.id]:
            if x["track"].id == vc.track.id:
                requester = x["requester"]
            break
        if requester is None:
            requester = Alternative_Context()
            requester.id = None
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
                # now be aware of queue looping so if we detects loop is queue then just call it's next function
                if vc.loop == Type_Loop.QUEUE:
                    await vc.play(vc.loop_queue.next())
                elif vc.loop == Type_Loop.SONG:
                    await vc.play(vc.track)
                else:
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
                await ctx.send(
                    embed=discord.Embed(
                        title="Vote",
                        description=f"{ctx.author.mention} has voted to skip this song. ({len(self.skip_votes[ctx.guild.id])}/2)",
                        color=discord.Color.green(),
                    )
                )
                if len(self.skip_votes[ctx.guild.id]) >= 2:
                    try:
                        async with async_timeout.timeout(2):
                            next_ = await vc.queue.get_wait()
                    except asyncio.TimeoutError:
                        next_ = None
                    if not next_:
                        return await ctx.send(
                            embed=discord.Embed(
                                title="Error",
                                description="There is no song left in queue.",
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

    @music.command()
    async def now(self, ctx: commands.Context):
        """
        Get the current song
        """
        if (
            not ctx.author.voice
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing() and not self.playing.get(
            ctx.guild.id, False
        ):
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
    async def add(
        self,
        ctx: commands.Context,
        query: str=None,
        source: Enum_Source = Enum_Source.YouTube,
    ):
        """
        Add music to a queue (incase of wavelink being bad)
        """
        if ctx.author.voice and not ctx.voice_client:
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
                        description="You must be in a voice channel and same channel as the bot to use this command.",
                        color=discord.Color.red(),
                    )
                )
        vc.loop = Type_Loop.NONE
        try:
            track = None
            if ctx.message.attachments:
                track = []
                count = 1
                for attachment in ctx.message.attachments:
                    if (False):
                        await ctx.send(
                            embed=discord.Embed(
                                title="Error",
                                description=f"Attachment number {count} has wrong content type.\nSkipping",
                            )
                        )
                        continue
                    count += 1
                    track.append(
                        (
                            (await wavelink.NodePool.get_node().get_tracks(
                                wavelink.Track, attachment.url
                            ))[0]
                        )
                    )
            elif "youtube.com" in query and "watch" in query:  # youtube link
                track = (
                    await wavelink.NodePool.get_node().get_tracks(
                        wavelink.YouTubeTrack, query
                    )
                )[0]
            elif "spotify.com" in query and ("playlist" in query or "album" in query):
                track = await wavelink.NodePool.get_node().get_tracks(
                    query=query, cls=spotify.SpotifyTrack
                )
            elif "spotify.com" in query and (
                not "playlist" in query or not "album" in query
            ):
                track = await wavelink.NodePool.get_node().get_tracks(
                    query=query, cls=spotify.SpotifyTrack
                )[0]
            elif "youtube.com" in query and "list" in query:
                track = await wavelink.NodePool.get_node().get_tracks(
                    query, cls=wavelink.YouTubePlaylist
                )
            elif "soundcloud.com" in query and not "sets" in query:
                track = (
                    await wavelink.NodePool.get_node().get_tracks(
                        query=query, cls=wavelink.SoundCloudTrack
                    )
                )[0]
            elif "soundcloud.com" in query and "sets" in query:
                track = await wavelink.NodePool.get_node().get_tracks(
                    query=query, cls=wavelink.SoundCloudTrack
                )
            elif " " in query:
                track = []
                for a in query.split(" "):
                    track.append((await wavelink.NodePool.get_node().get_tracks(
                                wavelink.Track, a
                            ))[0])
            else:
                if source == Enum_Source.YouTube:
                    track = await wavelink.YouTubeTrack.search(query, return_first=True)
                elif source == Enum_Source.SoundCloud:
                    track = (await wavelink.SoundCloudTrack.search(query))[0]
                elif source == Enum_Source.Spotify:
                    track = await spotify.SpotifyTrack.search(query, return_first=True)
                elif source == Enum_Source.SpotifyPlaylist:
                    track = await spotify.SpotifyTrack.search(query)
                elif source == Enum_Source.YouTubePlaylist:
                    track = await wavelink.YouTubeTrack.search(query)

        except wavelink.errors.LavalinkException as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"Lavalink server error.\n```py\nLavalinkException: {str(e)}\n```",
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
        if isinstance(track, (tuple, list)):
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
                    ),
                    delete_after=2,
                )

                await vc.queue.put_wait(track_)
        else:
            try:
                self.bindings[ctx.guild.id].append(
                    {
                        "track": track,
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

            await vc.queue.put_wait(track)
            await ctx.send(
                embed=discord.Embed(
                    title=f"Added {track.title} to the queue",
                    color=discord.Color.green(),
                )
            )

    @music.command()
    async def queue(self, ctx: commands.Context):
        if (
            not ctx.author.voice
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not ctx.voice_client.is_playing() and not self.playing.get(
            ctx.guild.id, False
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently playing.",
                    color=discord.Color.red(),
                )
            )
        vc: wavelink.Player = ctx.voice_client
        # now there's looping we should make list queue respond to looping
        if vc.loop == Type_Loop.NONE:
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
            description="There's currently {} songs in the queue.\nLimiting 50 queues to be shown on embed".format(
                len(vc.queue)
            ),
            color=discord.Color.green(),
        )
        for x in queue[:50]:
            embed.add_field(name=f"{count}", value=f"{x}", inline=False)
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
        i = f"{int(((vc.position / current_music.duration) * 100))}%"
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
                value=str(timedelta(seconds=int(vc.position))),
                inline=True,
            )
            .add_field(
                name="Listen at",
                value=vc.channel.mention,
            )
            .add_field(name="Author", value=current_music.author, inline=True)
            .add_field(name="URL", value=current_music.uri, inline=True)
            .add_field(name="Progress", value=i)
        )

    @music.command()
    async def remove(self, ctx: commands.Context, queue_index: int):
        vc: wavelink.Player = ctx.voice_client
        if (
            not ctx.author.voice
            or ctx.author.voice.channel.id != ctx.voice_client.channel.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must be in a voice channel and same channel as the bot to use this command.",
                    color=discord.Color.red(),
                )
            )
        if not vc.is_playing():
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="There is no song currently playing.",
                    color=discord.Color.red(),
                )
            )
        if queue_index > len(vc.queue):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="The queue index is out of range.",
                    color=discord.Color.red(),
                )
            )
        song = vc.queue[queue_index - 1]
        del vc.queue[queue_index - 1]
        await ctx.send(
            embed=discord.Embed(
                title="Removed",
                description="Removed {} at index {} from the queue.".format(
                    song, queue_index
                ),
                color=discord.Color.green(),
            )
        )

    @music.command()
    async def together(self, ctx: commands.Context, application: Enum_Applications):
        await ctx.send(
            embed=discord.Embed(
                title="Sucessfully created activity!",
                description=f"Click link below to started!\n{await self.together.create_link(ctx.author.voice.channel.id,application.value)}",
            )
        )


async def setup(bot):
    await bot.add_cog(Music(bot))
