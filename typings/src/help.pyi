import discord
from .utils import time as time
from .utils.paginator import Pages as Pages
from _typeshed import Incomplete
from discord.ext import commands, menus
from typing import Any, Dict, List, Optional, Union

class GroupHelpPageSource(menus.ListPageSource):
    group: Incomplete
    prefix: Incomplete
    title: Incomplete
    description: Incomplete
    def __init__(self, group: Union[commands.Group, commands.Cog], commands: List[commands.Command], *, prefix: str) -> None: ...
    async def format_page(self, menu, commands): ...

class HelpSelectMenu(discord.ui.Select['HelpMenu']):
    commands: Incomplete
    bot: Incomplete
    def __init__(self, commands: Dict[commands.Cog, List[commands.Command]], bot: commands.AutoShardedBot) -> None: ...
    async def callback(self, interaction: discord.Interaction): ...

class FrontPageSource(menus.PageSource):
    def is_paginating(self) -> bool: ...
    def get_max_pages(self) -> Optional[int]: ...
    index: Incomplete
    async def get_page(self, page_number: int) -> Any: ...
    def format_page(self, menu: HelpMenu, page): ...

class HelpMenu(Pages):
    def __init__(self, source: menus.PageSource, ctx: commands.Context) -> None: ...
    def add_categories(self, commands: Dict[commands.Cog, List[commands.Command]]) -> None: ...
    source: Incomplete
    current_page: int
    async def rebind(self, source: menus.PageSource, interaction: discord.Interaction) -> None: ...

class PaginatedHelpCommand(commands.HelpCommand):
    def __init__(self) -> None: ...
    async def on_help_command_error(self, ctx, error) -> None: ...
    def get_command_signature(self, command): ...
    async def send_bot_help(self, mapping): ...
    async def send_cog_help(self, cog) -> None: ...
    def common_command_formatting(self, embed_like, command) -> None: ...
    async def send_command_help(self, command) -> None: ...
    async def send_group_help(self, group): ...

class Help(commands.Cog):
    bot: Incomplete
    old_help_command: Incomplete
    def __init__(self, bot) -> None: ...
    @property
    def display_emoji(self) -> discord.PartialEmoji: ...
    def cog_unload(self) -> None: ...
    async def help(self, interaction: discord.Interaction, *, command: str = ...): ...

async def setup(bot) -> None: ...
