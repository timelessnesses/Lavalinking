import enum

import wavelink


class Enum_Source(enum.Enum):
    YouTube = "youtube"
    SoundCloud = "soundcloud"
    Spotify = "spotify"
    YouTubePlaylist = "youtube playlist"
    SpotifyPlaylist = "spotify playlist"


class Type_Loop(enum.Enum):
    """
    Enum for the loop type.
    """

    NONE = "none"
    SONG = "song"
    QUEUE = "queue"


class Enum_Applications(enum.Enum):
    """
    Enum for application for together command
    """

    watch_together = "youtube"
    poker_night = "poker"
    chess_in_the_park = "chess"
    letter_league = "letter-league"
    word_snack = "word-snack"
    sketch_heads = "sketch-heads"
    spellcast = "spellcast"
    awkword = "awkword"
    checkers_in_the_park = "checkers"
    blazing_8s = "blazing-8s"
    land_io = "land-io"
    putt_party = "putt-party"
    bobble_league = "bobble-league"
    ask_away = "ask-away"


class Enum_Filters(enum.Enum):
    blank = wavelink.filters.Filter
    flat_equalizer = wavelink.filters.Equalizer.flat
    boost_equalizer = wavelink.filters.Equalizer.boost
    metal_equalizer = wavelink.filters.Equalizer.metal
    piano_equalizer = wavelink.filters.Equalizer.piano
    karaoke = wavelink.filters.Karaoke
    equalizer = wavelink.filters.Equalizer
    timescale = wavelink.filters.Timescale
    tremolo = wavelink.filters.Tremolo
    vibrato = wavelink.filters.Vibrato
    rotation = wavelink.filters.Rotation
    distortion = wavelink.filters.Distortion
    channel_mix = wavelink.filters.ChannelMix
    channel_mix_mono = wavelink.filters.ChannelMix.mono
    channel_mix_only_left = wavelink.filters.ChannelMix.only_left
    channel_mix_only_right = wavelink.filters.ChannelMix.only_right
    channel_mix_full_left = wavelink.filters.ChannelMix.full_left
    channel_mix_full_right = wavelink.filters.ChannelMix.full_right
    channel_mix_switch = wavelink.filters.ChannelMix.switch
    low_pass = wavelink.filters.LowPass


needed_args = {
    Enum_Filters.karaoke: ["level", "mono level", "filter band", "filter width"],
    Enum_Filters.equalizer: [f"{x+1} band" for x in range(15)],
    Enum_Filters.timescale: ["speed", "pitch", "rate"],
    Enum_Filters.tremolo: ["frequency", "depth"],
    Enum_Filters.vibrato: ["frequency", "depth"],
    Enum_Filters.rotation: ["speed"],
    Enum_Filters.distortion: [
        "sin offset",
        "sin scale",
        "cos offset",
        "cos scale",
        "tan offset",
        "tan scale",
        "offset",
        "scale",
    ],
    Enum_Filters.channel_mix: [
        "left to left",
        "left to right",
        "right to left",
        "right to right",
    ],
    Enum_Filters.low_pass: ["smoothing"],
}

actual_class_name_for_class_methods = {
    Enum_Filters.flat_equalizer: Enum_Filters.equalizer,
    Enum_Filters.boost_equalizer: Enum_Filters.equalizer,
    Enum_Filters.metal_equalizer: Enum_Filters.equalizer,
    Enum_Filters.piano_equalizer: Enum_Filters.equalizer,
    Enum_Filters.channel_mix_mono: Enum_Filters.channel_mix,
    Enum_Filters.channel_mix_only_left: Enum_Filters.channel_mix,
    Enum_Filters.channel_mix_only_right: Enum_Filters.channel_mix,
    Enum_Filters.channel_mix_full_left: Enum_Filters.channel_mix,
    Enum_Filters.channel_mix_full_right: Enum_Filters.channel_mix,
    Enum_Filters.channel_mix_switch: Enum_Filters.channel_mix,
}
