import discord
import wavelink
from .utils.enums import Enum_Applications as Enum_Applications, Enum_Filters as Enum_Filters, Enum_Source as Enum_Source, Type_Loop as Type_Loop, actual_class_name_for_class_methods as actual_class_name_for_class_methods, needed_args as needed_args
from _typeshed import Incomplete
from discord.ext import commands

class Alternative_Context:
    def __init__(self, **kwargs) -> None: ...
    def __getattr__(self, name): ...
    def __setattr__(self, name, value) -> None: ...

class Music(commands.Cog):
    bot: Incomplete
    bindings: Incomplete
    skip_votes: Incomplete
    now_playing: Incomplete
    now_playing2: Incomplete
    def __init__(self, bot: commands.Bot) -> None: ...
    client: Incomplete
    async def connect(self) -> None: ...
    def cog_unload(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def on_wavelink_track_start(self, player: wavelink.Player, track: wavelink.Track): ...
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason: str): ...
    async def loop_time_update(self, track: wavelink.Track, msg: discord.Message, ctx: commands.Context, vc: wavelink.Player): ...
    async def cog_check(self, ctx: commands.Context): ...
    async def music(self, ctx: commands.Context): ...
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState): ...
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = ...): ...
    async def leave(self, ctx: commands.Context): ...
    async def play(self, ctx: commands.Context, source: Enum_Source = ..., *, query: str = ...): ...
    async def pause(self, ctx: commands.Context): ...
    async def stop(self, ctx: commands.Context): ...
    async def loop(self, ctx: commands.Context, type: Type_Loop): ...
    async def volume(self, ctx: commands.Context, volume: int = ...): ...
    async def skip(self, ctx: commands.Context): ...
    async def now(self, ctx: commands.Context): ...
    async def queue(self, ctx: commands.Context): ...
    async def info(self, current_music: wavelink.Track, ctx: commands.Context, vc: wavelink.Player): ...
    async def remove(self, ctx: commands.Context, queue_index: int): ...
    async def together(self, ctx: commands.Context, application: Enum_Applications): ...
    async def apply_single_filter(self, ctx: commands.Context, filters: Enum_Filters): ...
    async def apply_multiple_filters(self, ctx: commands.Context, json_string: str): ...

async def setup(bot) -> None: ...
