import enum
import typing

import wavelink.ext.spotify

Sources = typing.Literal["YouTube", "Spotify", "SoundCloud"]


class SpotifyTrackTypes(enum.Enum):
    track = wavelink.ext.spotify.SpotifyTrack
    playlist = wavelink.ext.spotify.SpotifyTrack  # multiple tracks.
