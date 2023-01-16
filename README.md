# Music bot with lavalink

A easy/configurable/lots of features for your need!  
This bot is designed to be stateless music bot (no database, no cache, no persistent data) so no needs for a database!

## How to host this???

### Normal

#### Requirement

- Python 3.8 or higher
- poetry (`pip install poetry`)

#### Procedure

1. Find your lavalink server [here](https://lavalink.darrennathanael.com/).

2. You can either make your own .env file and fill out these

```env
MUSIC_TOKEN=bot token
MUSIC_SPOTIFY_CLIENT_ID=spotify client id
MUSIC_SPOTIFY_CLIENT_SECRET=spotify client secret
MUSIC_LAVALINK_HOST=lavalink host (ip or domain)
MUSIC_LAVALINK_PORT=lavalink port
MUSIC_LAVALINK_PASSWORD=lavalink password
MUSIC_LAVALINK_HTTPS=lavalink https (true or false)
MUSIC_PREFIX=prefix
```

2.1 You can edit `config/config.py` to your own choice too

```py
from dotenv import load_dotenv

load_dotenv()
import os

token = "Bot token"
prefix = "bot prefix"
spotify_client_id = "spotify client id"  
spotify_client_secret = "spotify client secret"
lavalink_host = "lavalink host (ip or domain)"
lavalink_port = "lavalink port integer only"
lavalink_password = "lavalink password"
lavalink_is_https = True or False based on if you use https or not
```

3. Do `poetry install`

4. Do `poetry shell` to activate the virtual environment

5. Run `python3 bot.py`

6. Enjoy~

### Docker (pain)

1. Build it yourself with [`docker build .`](#building-docker) or clone it with `docker pull ghcr.io/timelessnesses/music-lavalink-bot:latest`

## Features

- [x] Using lavalink
- [x] Spotify supports
- [x] Youtube supports
- [x] Soundcloud supports
- [x] Music queue
- [x] Music loop
- [x] Skipping
- [x] Volume control
- [x] Music search
- [x] Live time update (Every Seconds)
- [x] Skip votes
- [ ] Filters
- [ ] Loop queues

## Recommendations
1. Please use this [lavalink jar file](https://github.com/davidffa/lavalink) for better results or find node that use this
