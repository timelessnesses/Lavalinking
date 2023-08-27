import enum
import typing

import wavelink.ext

Sources = typing.Literal["YouTube", "Spotify", "SoundCloud"]


class SpotifyTrackTypes(enum.Enum):
    track = wavelink.ext.spotify.SpotifyTrack
    playlist = wavelink.ext.spotify.SpotifyTrack  # multiple tracks.
