import re

import wavelink

from .types import SpotifyTrackTypes

REGEX_DETECT_URL = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+"
# regex (help) (thanks chatgpt)
YOUTUBE_VIDEO_REGEX = (
    r"^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w\-]{11}$"
)
YOUTUBE_PLAYLIST_REGEX = (
    r"^(https?:\/\/)?(www\.)?(youtube\.com\/playlist\?list=)[\w\-]+$"
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
) -> wavelink.Playable | wavelink.Playlist | SpotifyTrackTypes:
    """
    Detect source based on the URL pattern.
    """

    if re.findall(YOUTUBE_VIDEO_REGEX, url):
        return wavelink.YouTubeTrack
    elif re.findall(YOUTUBE_PLAYLIST_REGEX, url):
        return wavelink.YouTubePlaylist
    elif re.findall(SPOTIFY_SINGLE_REGEX, url):
        return SpotifyTrackTypes.track
    elif re.findall(SPOTIFY_PLAYLIST_REGEX, url):
        return SpotifyTrackTypes.playlist
    elif re.findall(SOUNDCLOUD_SINGLE_REGEX, url):
        return wavelink.SoundCloudTrack
    elif re.findall(SOUNDCLOUD_SETS_REGEX, url):
        return wavelink.SoundCloudPlaylist
    return wavelink.GenericTrack
