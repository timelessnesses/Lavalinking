import difflib
import sys
import io
from discord.utils import MISSING
import discord
from discord.ext import commands
import traceback


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        python_version = sys.version_info
        error_message = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        discord_version = discord.__version__
        file = MISSING
        if len(error_message) <= 4096:
            file = discord.File(io.StringIO(error_message), filename="errorlog.py")
            error_message = "Error is too long consider reading the errorlog.py file."
        if isinstance(error, commands.CommandNotFound):
            matches = difflib.get_close_matches(ctx.bot.commands, ctx.invoked_with)
            if len(matches) >= 2:
                await ctx.send(
                    embed=discord.Embed(
                        title="Did you mean...",
                        description=f"{', '.join(matches)} or {matches[0]}?",
                        color=discord.Color.yellow(),
                    )
                )
            elif len(matches) == 1:
                await ctx.send(
                    embed=discord.Embed(
                        title="Did you mean...",
                        description=f"{matches[0]}?",
                        color=discord.Color.yellow(),
                    )
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title="Command not found",
                        description=f"{ctx.invoked_with} is not a valid command.",
                        color=discord.Color.red(),
                    )
                )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=discord.Embed(
                    title="Missing argument",
                    description=f"{ctx.invoked_with} requires {error.param.name}.",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(
                    title="Bad argument",
                    description=f"{error.param.name} is not a valid.\n```py\nBadArgument: {str(error)}\n```",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.NotOwner):
            pass
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(
                embed=discord.Embed(
                    title="Permission denied",
                    description=f"You do not have the required permissions to use {ctx.invoked_with}.",
                    color=discord.Color.red(),
                )
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="Access denied",
                    description=f"I do not have permission to do that.",
                    color=discord.Color.red(),
                )
            )
        else:
            await ctx.send(
                embed=(
                    (
                        discord.Embed(
                            title="Error",
                            description=f"```py\n{error_message}\n```",
                            color=0xFF0000,
                        )
                    ).add_field(
                        name="Python Version",
                        value=f"{python_version[0]}.{python_version[1]}.{python_version[2]}",
                        inline=True,
                    )
                ).add_field(
                    name="Discord.py Version", value=discord_version, inline=True
                ),
                file=file,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
