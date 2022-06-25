CREATE TABLE IF NOT EXISTS config(
    server_id INTEGER PRIMARY KEY,
    lavalink_host TEXT DEFAULT 'lavalink.rukchadisa.live',
    lavalink_port INTEGER DEFAULT 80,
    lavalink_password TEXT DEFAULT 'youshallnotpass',
    stay_connected BOOLEAN DEFAULT FALSE,
    volume INTEGER DEFAULT 100
);
