import re
import typing

import wavelink

from .types import SpotifyTrackTypes

if typing.TYPE_CHECKING:
    from ..music import Playables

REGEX_DETECT_URL = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+"
# regex (help) (thanks chatgpt)
YOUTUBE_VIDEO_REGEX = (
    r"^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w\-]{11}"
)
YOUTUBE_PLAYLIST_REGEX = (
    r"^(https?:\/\/)?(www\.)?(youtube\.com\/playlist\?list=)[\w\-]+"
)
SPOTIFY_SINGLE_REGEX = r"^(https?:\/\/)?(open\.spotify\.com\/track\/)[a-zA-Z0-9]{22}(?:\?si=[a-zA-Z0-9]+)?$"
SPOTIFY_PLAYLIST_REGEX = (
    r"^(https?:\/\/)?(open\.spotify\.com\/playlist\/)[a-zA-Z0-9]{22}$"
)
SOUNDCLOUD_SETS_REGEX = (
    r"^(https?:\/\/)?(www\.)?soundcloud\.com\/[\w\-]+\/sets\/[\w\-]+$"
)
SOUNDCLOUD_SINGLE_REGEX = r"^(https?:\/\/)?(www\.)?soundcloud\.com\/[\w\-]+\/[\w\-]+$"  # FIXME: this matches everything with https://soundcloud.com/anything/anything


def detect_url(url: str) -> bool:
    return len(re.findall(REGEX_DETECT_URL, url)) != 0


def detect_source(
    url: str,
) -> "Playables":
    """
    Detect source based on the URL pattern.
    """

    if re.findall(YOUTUBE_VIDEO_REGEX, url):  # ??????
        return wavelink.YouTubeTrack  # type: ignore
    elif re.findall(YOUTUBE_PLAYLIST_REGEX, url):
        return wavelink.YouTubePlaylist  # type: ignore
    elif re.findall(SPOTIFY_SINGLE_REGEX, url):
        return SpotifyTrackTypes.track  # type: ignore
    elif re.findall(SPOTIFY_PLAYLIST_REGEX, url):
        return SpotifyTrackTypes.playlist  # type: ignore
    elif re.findall(SOUNDCLOUD_SINGLE_REGEX, url):
        return wavelink.SoundCloudTrack  # type: ignore
    elif re.findall(SOUNDCLOUD_SETS_REGEX, url):
        return wavelink.SoundCloudPlaylist  # type: ignore
    return wavelink.GenericTrack  # type: ignore
