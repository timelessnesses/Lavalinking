import wavelink
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

load_dotenv()
import os


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        asyncio.run(self.connect())

    async def connect(self):
        await self.bot.wait_until_ready()
        client: wavelink.ext.spotify.SpotifyClient = None
        if os.getenv("MUSIC_SPOTIFY_CLIENT_ID") and os.getenv(
            "MUSIC_SPOTIFY_CLIENT_SECRET"
        ):
            client = wavelink.ext.spotify.SpotifyClient(
                os.getenv("MUSIC_SPOTIFY_CLIENT_ID"),
                os.getenv("MUSIC_SPOTIFY_CLIENT_SECRET"),
            )
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=os.getenv("MUSIC_LAVALINK_HOST"),
            port=int(os.getenv("MUSIC_LAVALINK_PORT")),
            password=os.getenv("MUSIC_LAVALINK_PASSWORD"),
            spotify_client=client,
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
        if not ctx.guild.me.voice:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I am already in {}. And due to discord's limitation I couldn't join multiple voice chats.".format(
                        ctx.guild.me.voice.channel.mention
                    ),
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
    async def play(self, ctx: commands.Context, *, query: str):
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
            embed=info(current_music, ctx.author.voice.channel.mention)
        )

    def info(self, current_music: wavelink.Track, vc: str):

