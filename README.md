# Lavalinking (REWRITE)

A easy/configurable/lots of features for your need!  
This bot is designed to be stateless music bot (no database, no cache, no persistent data) so no needs for a database!

## Status

This project is now unmaintained with too many bugs, and I am kinda not interested in it anymore. The actual bot will also be shut down, thanks for using it.

## How to host this???

### Normal

#### Requirement

- Python 3.10 or higher
- poetry (`pip install poetry`)
- A lavalink server (either locally host it or find one [here](https://lavalink.darrennathanael.com/) or if you are lazy go ahead use `lavalink.api.timelessnesses.me` with port of 80 and password `youshallnotpass` and it's not ssl)

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

3. Do `make install`

4. Do `make run`

### Docker (BYO Image)

1. Configure stuffs inside `config/config.py`
2. Build image with `make build_image`
3. Run with `docker run lavalinking_dev:latest` (Add `-d` flag for detaching from the console and run it in background)

### Docker (GitHub Pre-built Image)

1. Create `.env` file and configure stuff as same as one in [Step 2 Procedure](#procedure)
2. Run `docker run --env-file=.env ghcr.io/timelessnesses/lavalinking:latest` (Add `-d` flag for detaching from the console and run it in background)

### Docker (Lavalink server included)

1. Clone the repository
2. Create `.env` file and configure stuff as same as one in [Step 2 Procedure](#procedure)
3. Run `docker compose up` (Add `-d` flag for detaching from the console and run it in background)

## Features

- [x] Using lavalink
- [x] Spotify supports
- [x] Youtube supports
- [x] Soundcloud supports
- [x] Music queue
- [x] Music loop
- [x] Skipping
- [x] Volume control (up to 1000)
- [x] Music search
- [x] Live time update (Every 5 Seconds)
- [x] Skip votes
- [ ] Filters
- [x] Loop queues
- [x] Playing from file attachment and direct audio/video URL
- [x] Assuring command argument have the appropiate type
- [x] Slash command/Prefix command

## Recommendations
1. Please use this [lavalink jar file](https://github.com/davidffa/lavalink) for better results or find node that use this

## status
Lavalinkable is now in stable status. Will work on issues that were posted
