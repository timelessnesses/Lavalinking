import typing

import wavelink
from discord.ext import commands

from config import config


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.node = wavelink.Node(
            uri=f"{'https' if config.lavalink_is_https else 'http'}://{config.lavalink_host}:{config.lavalink_port}",
            password=config.lavalink_password,
        )


async def setup(bot: commands.Bot) -> typing.Optional["Music"]:
    pass
