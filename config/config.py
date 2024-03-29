from dotenv import load_dotenv

load_dotenv()
import os

token = os.getenv("MUSIC_TOKEN")
prefix = os.getenv("MUSIC_PREFIX", "l!")
spotify_client_id = os.getenv("MUSIC_SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("MUSIC_SPOTIFY_CLIENT_SECRET")
lavalink_host = os.getenv("MUSIC_LAVALINK_HOST")
lavalink_port = os.getenv("MUSIC_LAVALINK_PORT")
lavalink_password = os.getenv("MUSIC_LAVALINK_PASSWORD")
lavalink_is_https = True if int(os.getenv("MUSIC_LAVALINK_HTTPS", 0)) else False
owners_id = os.getenv("MUSIC_OWNERS_ID", ",").split(",")
