import argparse
import typing
from time import perf_counter as pc

import discord
from discord.ext import commands
from dotenv import load_dotenv
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

load_dotenv()
import asyncio
import datetime
import logging
import os
import subprocess
import traceback

from config import config

formatting = logging.Formatter("[%(asctime)s] - [%(levelname)s] [%(name)s] %(message)s")

logging.basicConfig(
    level=logging.NOTSET,
    format="[%(asctime)s] - [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

log = logging.getLogger("lavalinking.bot")
log.setLevel(logging.DEBUG)

try:
    os.mkdir("logs")
except FileExistsError:
    pass
log_path = f"logs/bot_{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.log"
with open(log_path, "w") as f_:
    f_.write("")
f = logging.FileHandler(log_path, "w")
f.setFormatter(formatting)
f.setLevel(logging.DEBUG)

logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("wavelink").setLevel(logging.WARNING)
logging.getLogger("watchdog").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.INFO)

# also redirect to files :P
log.addHandler(f)
logging.getLogger("discord").addHandler(f)
logging.getLogger("wavelink").addHandler(f)
logging.getLogger("watchdog").addHandler(f)
logging.getLogger("asyncio").addHandler(f)
logging.getLogger("lavalinking.src").addHandler(f)

bot = commands.AutoShardedBot(
    command_prefix=config.prefix,
    intents=discord.Intents.all(),
    owners_id=config.owners_id,
)
bot.log = log  # type: ignore

observer = Observer()

"https://github.com/gorakhargosh/watchdog/issues/1003#issuecomment-1689069256"


class _LastEvent(typing.TypedDict):
    time: float
    event: FileSystemEvent | None


class _DuplicateEventLimiter:
    """Duplicate event limiter.

    This class is responsible for limiting duplicated event detection. It works
    by comparing the timestamp of the previous event (if existent) to the
    current one, as well as the event itself. If the difference between the
    timestamps is less than a threshold and the events are the same, the event
    is considered a duplicate.
    """

    _DUPLICATE_THRESHOLD: float = 0.05
    _DUPLICATE_logger = logging.getLogger("lavalinking.bot._DuplicateEventLimiter")

    def __init__(self) -> None:
        """Initialize a _DuplicateEventLimiter instance."""
        # Dummy event:
        self._last_event: "_LastEvent" = {"time": 0, "event": None}

    def _is_duplicate(self, event: FileSystemEvent) -> bool:
        """Determine if an event is a duplicate.

        Args:
            event (watchdog.events.FileSystemEvent): event to check.

        Returns:
            bool: True if the event is a duplicate, False otherwise.
        """
        self._DUPLICATE_logger.debug(f"Checking duplicate event: {event}")
        is_duplicate: bool = (
            pc() - self._last_event["time"] < self._DUPLICATE_THRESHOLD
            and self._last_event["event"] == event
        )

        self._DUPLICATE_logger.debug(
            f"The event is {'not ' if not is_duplicate else ''}duplicated."
        )

        self._last_event = {"time": pc(), "event": event}

        self._DUPLICATE_logger.debug("Saved last event.")

        return is_duplicate


class FileHandler(FileSystemEventHandler):
    logger = logging.getLogger("lavalinking.bot.FileHandler.on_modified")

    def on_modified(self, event: FileSystemEvent):
        if event.src_path.endswith(".py"):
            self.logger.info(f"File changed: {event.src_path}")
            self.logger.info("Reloading...")
            path = event.src_path.replace("\\", "/").replace("/", ".")[:-3]
            try:
                asyncio.run(bot.reload_extension(path))
                self.logger.info(f"Reloaded {path}")
            except Exception as e:
                self.logger.error(f"Failed to reload {path}")
                self.logger.error(e)
                self.logger.error(traceback.format_exc())


observer.schedule(FileHandler(), path="src", recursive=False)


def get_git_revision_short_hash() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .decode("ascii")
        .strip()
    )


def get_version():
    if bool(int(os.getenv("DOCKERIZED", 0))):
        bot.version_ = f"Containerized ({os.getenv('REVISION')})"  # type: ignore
        return
    is_updated = subprocess.check_output("git status", shell=True).decode("ascii")

    if "modified" in is_updated:
        is_updated = None
    elif (
        "up to date" in is_updated
        or "nothing to commit, working tree clean" in is_updated
    ):
        is_updated = True
    else:
        is_updated = False

    if is_updated:
        bot.version_ = f"latest ({get_git_revision_short_hash()})"  # type: ignore
    elif is_updated is None:
        bot.version_ = f"{get_git_revision_short_hash()} (modified)"  # type: ignore
    else:
        bot.version_ = f"old ({get_git_revision_short_hash()}) - not up to date"  # type: ignore


@bot.event
async def on_ready():
    log.info("Logged in as")
    log.info(bot.user.name)  # type: ignore
    log.info(bot.user.id)  # type: ignore
    log.info("------")
    await bot.change_presence(activity=discord.Game(name=f"{config.prefix}help"))
    await bot.tree.sync()


async def main():
    # raise Exception
    try:
        started = False
        while not started:
            async with bot:
                for extension in os.listdir("src"):
                    if extension.endswith(".py") and not extension.startswith("_"):
                        await bot.load_extension(f"src.{extension[:-3]}")
                        log.info(f"Loaded extension {extension[:-3]}")
                await bot.load_extension("jishaku")
                log.info("Loaded jishaku")
                bot.start_time = datetime.datetime.utcnow()  # type: ignore
                get_version()
                log.info(
                    f"Started with version {bot.version_} and started at {bot.start_time}"  # type: ignore
                )
                try:
                    await bot.start(config.token)
                except discord.errors.HTTPException:
                    log.exception("You likely got ratelimited or bot's token is wrong")
                started = True  # break loop
    except KeyboardInterrupt:
        log.info("Exiting...")


def starter() -> typing.NoReturn:
    args = argparse.ArgumentParser(description="A music bot with a lavalink support.")

    args.add_argument(
        "-d", "--debug", action="store_true", help="Debug mode. (Sensitive data!)"
    )
    args.add_argument(
        "-r",
        "--reloader",
        action="store_true",
        help="File reloader. (For development/Quick reloading without jishaku reload module.)",
    )

    parsed = args.parse_args()
    reloader = False

    if parsed.debug:
        logging.getLogger("discord").setLevel(logging.DEBUG)
        logging.getLogger("wavelink").setLevel(logging.DEBUG)
        logging.getLogger("watchdog").setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
    if parsed.reloader:
        reloader = True
        observer.run()
        log.info("Started file watcher. (0.5 seconds ratelimiting.)")
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error("An unhandled error has occured. (%s)", e.__class__.__name__)
        logging.error("%s", "".join(traceback.format_exception(e)))
        observer.stop() if reloader else None
        logging.error("Exiting gracefully.")
        exit(1)
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt recieved. Exiting gracefully.")
        observer.stop() if reloader else None
        exit(0)
    else:
        observer.stop() if reloader else None
        logging.info("Exiting gracefully.")
        exit(0)


if __name__ == "__main__":
    starter()
