from _typeshed import Incomplete
from discord.ext import commands

from .formats import human_join as human_join
from .formats import plural as plural

units: Incomplete

class ShortTime:
    compiled: Incomplete
    dt: Incomplete
    def __init__(self, argument, *, now: Incomplete | None = ...) -> None: ...
    @classmethod
    async def convert(cls, ctx, argument): ...

class HumanTime:
    calendar: Incomplete
    dt: Incomplete
    def __init__(self, argument, *, now: Incomplete | None = ...) -> None: ...
    @classmethod
    async def convert(cls, ctx, argument): ...

class Time(HumanTime):
    dt: Incomplete
    def __init__(self, argument, *, now: Incomplete | None = ...) -> None: ...

class FutureTime(Time):
    def __init__(self, argument, *, now: Incomplete | None = ...) -> None: ...

class UserFriendlyTime(commands.Converter):
    converter: Incomplete
    default: Incomplete
    def __init__(
        self, converter: Incomplete | None = ..., *, default: Incomplete | None = ...
    ) -> None: ...
    arg: Incomplete
    async def check_constraints(self, ctx, now, remaining): ...
    def copy(self): ...
    async def convert(self, ctx, argument): ...

def human_timedelta(
    dt,
    *,
    source: Incomplete | None = ...,
    accuracy: int = ...,
    brief: bool = ...,
    suffix: bool = ...
): ...
def format_relative(dt): ...
