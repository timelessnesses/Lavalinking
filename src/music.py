import datetime
import logging
import typing

import discord
import wavelink
import wavelink.ext.spotify
from discord.ext import commands

from config import config

from .utils.exceptions import LavalinkingException
from .utils.regexes import detect_source, detect_url
from .utils.types import Sources, SpotifyTrackTypes

Playables = typing.TypeVar(
    "Playables",
    type[wavelink.YouTubeTrack],
    type[wavelink.YouTubePlaylist],
    type[wavelink.SoundCloudTrack],
    type[wavelink.SoundCloudPlaylist],
    type[wavelink.GenericTrack],
    type[wavelink.ext.spotify.SpotifyTrack],
    type[wavelink.Playable],
    wavelink.YouTubeTrack,
    wavelink.YouTubePlaylist,
    wavelink.SoundCloudTrack,
    wavelink.SoundCloudPlaylist,
    wavelink.GenericTrack,
    wavelink.ext.spotify.SpotifyTrack,
    wavelink.Playable,
)  # Vomit

Tracks = (
    wavelink.YouTubeTrack
    | wavelink.YouTubePlaylist
    | wavelink.SoundCloudTrack
    | wavelink.SoundCloudPlaylist
    | wavelink.GenericTrack
    | wavelink.ext.spotify.SpotifyTrack
    | wavelink.Playable
)


class Music(commands.Cog):
    # stuffs
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
        # self.bind_ctx: dict[discord.Guild, wavelink.Player] = {}
        self.playings: dict[
            discord.Guild,
            wavelink.YouTubeTrack
            | wavelink.YouTubePlaylist
            | wavelink.SoundCloudTrack
            | wavelink.SoundCloudPlaylist
            | wavelink.GenericTrack
            | wavelink.ext.spotify.SpotifyTrack
            | wavelink.Playable,
        ] = {}
        self.skips: dict[discord.Guild, list[discord.Member]] = {}

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

    async def cog_check(self, ctx: commands.Context):  # type: ignore
        if ctx.guild is None:
            return False
        return True

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        self.logger.info(f"Successfully connected to node: {node.uri}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, pl: wavelink.TrackEventPayload) -> None:
        if pl.player.guild is None:
            return
        self.playings[pl.player.guild] = pl.track
        self.skips[pl.player.guild].clear()

    @commands.hybrid_command()  # type: ignore
    async def join(
        self,
        ctx: commands.Context,
        channel: typing.Optional[
            typing.Union[discord.VoiceChannel, discord.StageChannel]
        ] = None,
    ) -> typing.Optional[wavelink.Player]:
        """
        Make the bot join to the specified voice channel (supply channel argument is required if you are not in any voice chat in this server.)
        """

        try:
            channel = channel or ctx.author.voice.channel  # type: ignore[union-attr]
        except AttributeError:
            await ctx.reply(embed=self.generate_error("Voice chat argument required."))
            return None

        vc = await channel.connect(cls=wavelink.Player)  # type: ignore[union-attr]
        return vc

    async def get_vc(self, ctx: commands.Context) -> wavelink.Player:
        """
        Get voice chat.
        """

        vc: typing.Optional[wavelink.Player] = None  # type: ignore

        if ctx.voice_client:
            vc: wavelink.Player = ctx.voice_client  # type: ignore
        elif wavelink.NodePool.get_connected_node().get_player(ctx.guild.id):  # type: ignore[union-attr]
            vc: wavelink.Player = wavelink.NodePool.get_connected_node().get_player(
                ctx.guild.id  # type: ignore[union-attr]
            )
        elif ctx.author.voice:  # type: ignore
            vc: wavelink.Player = await self.join(ctx.author.voice)  # type: ignore
        if vc is None:
            await ctx.reply(
                embed=self.generate_error("No voice chat instance detected.")
            )
            raise LavalinkingException("Voice chat not found!")
        return vc

    async def get_track(
        self,
        source: wavelink.Playable | wavelink.Playlist | SpotifyTrackTypes,
        query: str,
    ) -> wavelink.Playable | list[wavelink.Playable] | None:
        """
        Get a track based on the source.
        """

        node = wavelink.NodePool.get_connected_node()
        match source:
            case wavelink.YouTubeTrack:
                return (await node.get_tracks(wavelink.YouTubeTrack, query))[0]
            case wavelink.YouTubePlaylist:
                return await node.get_playlist(wavelink.YouTubePlaylist, query)  # type: ignore
            case SpotifyTrackTypes.track:
                return (await wavelink.ext.spotify.SpotifyTrack.search(query))[0]  # type: ignore
            case SpotifyTrackTypes.playlist:
                return await wavelink.ext.spotify.SpotifyTrack.search(query)  # type: ignore
            case wavelink.SoundCloudTrack:
                return (await node.get_tracks(wavelink.SoundCloudTrack, query))[0]
            case wavelink.SoundCloudPlaylist:
                return await node.get_playlist(wavelink.SoundCloudPlaylist, query)  # type: ignore
            case wavelink.GenericTrack:
                return (await node.get_tracks(wavelink.GenericTrack, query))[0]
            case _:
                raise ValueError("Track type is not supported: {}".format(source))

    async def search_tracks(
        self, source: Playables, query: str
    ) -> list[type[Playables]]:
        node = wavelink.NodePool.get_connected_node()
        return await source.search(query, node=node)  # type: ignore

    def convert_source(
        self, source: Sources, playlist: bool
    ) -> (
        wavelink.Playable
        | wavelink.Playlist
        | wavelink.ext.spotify.SpotifyTrack
        | wavelink.GenericTrack
    ):
        match source, playlist:
            case "YouTube", False:
                return wavelink.YouTubeTrack  # type: ignore
            case "YouTube", True:
                return wavelink.YouTubePlaylist  # type: ignore
            case "Spotify", _:
                return wavelink.ext.spotify.SpotifyTrack  # type: ignore
            case "SoundCloud", False:
                return wavelink.SoundCloudTrack  # type: ignore
            case "SoundCloud", True:
                return wavelink.SoundCloudPlaylist  # type: ignore
            case _, _:
                raise ValueError("Invalid source string: {}".format(source))
        raise ValueError(
            "Invalid source string: {}".format(source)
        )  # mypy doesn't know the default will raise error.

    async def get_song_by_url(self, source: Playables, url: str) -> type[Playables]:
        return (await source.search(url))[0]  # type: ignore

    def build_selection_tracks(self, tracks: list[wavelink.Playable]) -> discord.Embed:
        embed = discord.Embed(title="Tracks (Limited to 10)")
        for no, track in enumerate(tracks[:10], 1):
            embed.add_field(
                name=f"{no}. {track.author}", value=track.title, inline=True
            )
        return embed

    def generate_success_embed(self, title: str) -> discord.Embed:
        return discord.Embed(title=title, color=discord.Color.green())

    @commands.hybrid_command()  # type: ignore
    async def play(
        self,
        ctx: commands.Context,
        query: str,
        source: Sources = "YouTube",
        playlist: bool = False,
        autoadd: bool = False,
    ) -> None:
        vc = await self.get_vc(ctx)
        if detect_url(query):
            source = detect_source(query)  # type: ignore[assignment]
            await self.play_song(vc, (await self.get_song_by_url(source, query)))  # type: ignore
            return
        tracks = (await self.search_tracks(self.convert_source(source, playlist), query))[:10]  # type: ignore
        await ctx.reply(embed=self.build_selection_tracks(tracks))
        try:
            track: wavelink.Playable = tracks[
                int(
                    (
                        await self.bot.wait_for(
                            "message", check=lambda x: x.author == ctx.author
                        )
                    ).content
                )
                - 1
            ]
        except ValueError:
            await ctx.reply(embed=self.generate_error("Invalid index! Exiting"))
        except IndexError:
            await ctx.reply(embed=self.generate_error("Out of index bound! Exiting"))
        else:
            await self.play_song(vc, track)
            await ctx.reply(
                embed=self.generate_success_embed(f"Successfully added {str(track)}")
            )

    async def play_song(self, vc: wavelink.Player, track: Playables) -> None:
        if vc.is_playing():
            await vc.queue.put_wait(track)  # type: ignore
            return
        await vc.play(track)  # type: ignore

    @commands.command()  # type: ignore
    async def pause(
        self, ctx: commands.Context, force: typing.Optional[bool] = None
    ) -> None:
        vc = await self.get_vc(ctx)
        if force is not None:
            match force, vc.is_paused():
                case False, False:
                    await ctx.reply(embed=self.generate_error("Already playing!"))
                    await vc.pause()
                    return
                case False, True:
                    await ctx.reply(embed=self.generate_success_embed("Resuming!"))
                    await vc.pause()
                    return
                case True, True:
                    await ctx.reply(embed=self.generate_error("Already paused!"))
                    return
                case True, False:
                    await ctx.reply(embed=self.generate_success_embed("Pausing!"))
                    await vc.pause()
                    return
        await vc.pause()
        await ctx.reply(
            embed=self.generate_success_embed(
                f"Successfully {'paused' if vc.is_paused() else 'resumed'}."  # type: ignore
            )
        )

    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        vc = await self.get_vc(ctx)
        await vc.stop()
        await ctx.reply(embed=self.generate_success_embed("Stopped!"))

    @commands.hybrid_command()  # type: ignore
    async def volume(
        self, ctx: commands.Context, volume: discord.app_commands.Range[int, 0, 1000]
    ) -> None:
        vc = await self.get_vc(ctx)
        await vc.set_volume(volume)
        await ctx.reply(
            embed=self.generate_success_embed(
                f"Successfully changed volume to: {volume}"
            )
        )

    @commands.hybrid_command()  # type: ignore
    async def leave(self, ctx: commands.Context) -> None:
        vc = await self.get_vc(ctx)
        await vc.disconnect()
        await ctx.reply(embed=self.generate_success_embed("Left!"))

    @commands.hybrid_command()  # type: ignore
    async def now(self, ctx: commands.Context) -> None:
        vc = await self.get_vc(ctx)
        track = self.playings.get(ctx.guild)  # type: ignore
        if track:
            await ctx.reply(embed=self.generate_song_embed(track, vc))
        else:
            await ctx.reply(
                embed=self.generate_error(
                    "Cannot get current playing track. Is it playing?"
                )
            )

    def generate_song_embed(
        self,
        track: wavelink.YouTubeTrack
        | wavelink.YouTubePlaylist
        | wavelink.SoundCloudTrack
        | wavelink.SoundCloudPlaylist
        | wavelink.GenericTrack
        | wavelink.ext.spotify.SpotifyTrack
        | wavelink.Playable,
        player: wavelink.Player,
    ) -> discord.Embed:
        author = ""
        try:
            author: str = track.author  # type: ignore
        except AttributeError:
            author = ", ".join(track.artists)  # type: ignore
        try:
            pos = track.position  # type: ignore
        except AttributeError:
            pass
        e = discord.Embed(
            title=f"Now Playing: {author} - {track.title}",
            description=f"""
- Author{"s" if "," in author else ""}: {author}
- Title: {track.title}
- Progress: {self.convert_dur_pos_to_time(player.position,track.length)}
    """,
        )
        return e

    def convert_dur_pos_to_time(
        self, pos: typing.Optional[float], length: float
    ) -> str:
        d_length = datetime.timedelta(milliseconds=length)
        if pos:
            d_pos = datetime.timedelta(milliseconds=pos)
            return f"{str(d_pos)}/{str(d_length)} ({str(d_length - d_pos)}) ({100 * d_pos.total_seconds() / d_length.total_seconds()}%)"
        return f"{str(d_length)}"

    @commands.hybrid_command()  # type: ignore
    async def skip(self, ctx: commands.Context) -> None:
        vc = await self.get_vc(ctx)
        skipvotes = self.skips[ctx.guild]  # type: ignore
        if ctx.author in skipvotes:
            await ctx.reply(
                embed=self.generate_error("You are already voted for skipping!")
            )
            return
        self.skips[ctx.guild].append(ctx.author)  # type: ignore
        if len(self.skips[ctx.guild]) >= 3:  # type: ignore
            await vc.stop(force=True)
            return
        await ctx.reply(
            embed=self.generate_success_embed(
                "Successfully added you in to the skip votes!"
            )
        )

    @commands.hybrid_command()  # type: ignore
    async def queue(self, ctx: commands.Context) -> None:
        vc = await self.get_vc(ctx)
        if len(vc.queue) == 0:
            await ctx.reply(embed=self.generate_error("No more songs in queue!"))
            return
        e = discord.Embed(title="Queue (Limited to 10 songs)")
        c = 0
        for track in vc.queue:
            e.add_field(
                name=f"{track.__dict__.get('author', ', '.join(track.__dict__.get('artists', [])))}",
                value=f"{track.title}",
            )
            c += 1
            if c == 10:
                break
        await ctx.reply(embed=e)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
