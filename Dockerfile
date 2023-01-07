FROM python:3.9-alpine
WORKDIR /bot
ARG token
ARG spotify_client_id
ARG spotify_client_secret
ARG lavalink_host="localhost"
ARG lavalink_port="2333"
ARG lavalink_password="youshallnotpass"
ARG lavalink_https="false"
ARG prefix="m1"
ARG owner_ids=""
ENV MUSIC_TOKEN=$token
ENV MUSIC_SPOTIFY_CLIENT_ID=$spotify_client_id
ENV MUSIC_SPOTIFY_CLIENT_SECRET=$spotify_client_secret
ENV MUSIC_LAVALINK_HOST=$lavalink_host
ENV MUSIC_LAVALINK_PORT=$lavalink_port
ENV MUSIC_LAVALINK_PASSWORD=$lavalink_password
ENV MUSIC_LAVALINK_HTTPS=$lavalink_https
ENV MUSIC_PREFIX=$prefix
ENV MUSIC_OWNER_IDS=$owner_ids
RUN pip install --upgrade pip
RUN pip install poetry
RUN apk add gcc build-base linux-headers g++ wget
RUN poetry install
RUN apk del gcc build-base linux-headers g++ # save space :)
COPY . .
RUN pip install requests
RUN python3 bin/lavalink_check.py
CMD make