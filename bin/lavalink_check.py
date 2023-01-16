"""
this script only supports linux only.
"""
import os

lavalink_download_url = (
    "https://github.com/freyacodes/Lavalink/releases/download/3.6.2/Lavalink.jar"
)

install_zulu_command = """
    echo "Installing Zulu JDK 19"
    wget https://cdn.azul.com/zulu/bin/zulu19.30.11-ca-jdk19.0.1-linux_musl_x64.tar.gz
    sha256sum zulu19.30.11-ca-jdk19.0.1-linux_musl_x64.tar.gz
    if [ $? -eq 0 ]; then
        echo "Checksum verified"
        tar -xzvf zulu19.30.11-ca-jdk19.0.1-linux_musl_x64.tar.gz
        export PATH=$PATH:$(pwd)/zulu19.30.11-ca-jdk19.0.1-linux_musl_x64/bin
    else
        echo "Checksum failed"
        exit 1
    fi
"""

install_lavalink_command = f"""
if [ ! -f Lavalink.jar ]; then
    echo "Downloading Lavalink.jar"
    wget {lavalink_download_url}
fi
"""

default_lavalink_config = """
server: # REST and WS server
  port: 2333
  address: 0.0.0.0
lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
      local: false
    bufferDurationMs: 400 # The duration of the NAS buffer. Higher values fare better against longer GC pauses. Minimum of 40ms, lower values may introduce pauses.
    frameBufferDurationMs: 5000 # How many milliseconds of audio to keep buffered
    opusEncodingQuality: 10 # Opus encoder quality. Valid values range from 0 to 10, where 10 is best quality but is the most expensive on the CPU.
    resamplingQuality: LOW # Quality of resampling operations. Valid values are LOW, MEDIUM and HIGH, where HIGH uses the most CPU.
    trackStuckThresholdMs: 10000 # The threshold for how long a track can be stuck. A track is stuck if does not return any audio data.
    useSeekGhosting: true # Seek ghosting is the effect where whilst a seek is in progress, the audio buffer is read from until empty, or until seek is ready.
    youtubePlaylistLoadLimit: 6 # Number of pages at 100 each
    playerUpdateInterval: 5 # How frequently to send player updates to clients, in seconds
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true
    gc-warnings: true
    #ratelimit:
      #ipBlocks: ["1.0.0.0/8", "..."] # list of ip blocks
      #excludedIps: ["...", "..."] # ips which should be explicit excluded from usage by lavalink
      #strategy: "RotateOnBan" # RotateOnBan | LoadBalance | NanoSwitch | RotatingNanoSwitch
      #searchTriggersFail: true # Whether a search 429 should trigger marking the ip as failing
      #retryLimit: -1 # -1 = use default lavaplayer value | 0 = infinity | >0 = retry will happen this numbers times
    #youtubeConfig: # Required for avoiding all age restrictions by YouTube, some restricted videos still can be played without.
      #email: "" # Email of Google account
      #password: "" # Password of Google account
    #httpConfig: # Useful for blocking bad-actors from ip-grabbing your music node and attacking it, this way only the http proxy will be attacked
      #proxyHost: "localhost" # Hostname of the proxy, (ip or domain)
      #proxyPort: 3128 # Proxy port, 3128 is the default for squidProxy
      #proxyUser: "" # Optional user for basic authentication fields, leave blank if you don't use basic auth
      #proxyPassword: "" # Password for basic authentication

metrics:
  prometheus:
    enabled: true
    endpoint: /metrics

sentry:
  dsn: ""
  environment: ""
#  tags:
#    some_key: some_value
#    another_key: another_value

logging:
  file:
    path: ./logs/

  level:
    root: INFO
    lavalink: INFO

  logback:
    rollingpolicy:
      max-file-size: 1GB
      max-history: 30
"""

install_lavalink_service = """
[Unit]
Description=Lavalink server
After=network.target

[Service]
Restart=always
user=root
WorkingDirectory=/root
ExecStart=/usr/bin/java -jar Lavalink.jar

[Install]
WantedBy=multi-user.target
"""


def check_env_vars():
    print("Verifying Enviroment Variables")
    expect = [
        "MUSIC_TOKEN",
        "MUSIC_SPOTIFY_CLIENT_ID",
        "MUSIC_SPOTIFY_CLIENT_SECRET",
        "MUSIC_LAVALINK_HOST",
        "MUSIC_LAVALINK_PORT",
        "MUSIC_LAVALINK_PASSWORD",
        "MUSIC_LAVALINK_HTTPS",
        "MUSIC_PREFIX",
        "MUSIC_OWNERS_ID",
    ]
    for key, val in os.environ.items():
        if key in expect and not val:  # docker treats empty strings as unset
            expect.remove(key)

    assert len(expect) > 0, "Missing environment variables: " + ", ".join(expect)
    print("All environment variables are set")


def check_lavalink():
    print(
        "Checking if any lavalink related enviroment variables are default to their values"
    )
    expect = {
        "MUSIC_LAVALINK_HOST": "localhost",
        "MUSIC_LAVALINK_PORT": 2333,
        "MUSIC_LAVALINK_PASSWORD": "youshallnotpass",
        "MUSIC_LAVALINK_HTTPS": "false",
    }
    for key, val in os.environ.items():
        if key in expect and val == expect[key]:
            del expect[key]  # likely to be a default value, so remove it from the list
            return

    # if its default value then likely going to setup local lavalink server
    if len(expect) == 0:
        print(
            "All enviroment variables are not default to their values. Assuming you have a lavalink server running"
        )
        return
    print(
        "Some enviroment variables are default to their values. Assuming you want to setup a local lavalink server inside this container"
    )
    install_lavalink()
    print("Installed lavalink server. Now starting it")
    run_lavalink()
    print("Successfully started lavalink server")


def install_zulu_jdk():
    print("Checking if any java is installed")
    if not os.system(
        "java -version"
    ):  # already have something java installed so i don't really care
        return
    print("No java installed. Installing Zulu JDK 19")
    assert not os.system(install_zulu_command), "Failed to install Zulu JDK 19"


def install_lavalink():
    install_zulu_jdk()
    print("Installed Zulu JDK 19. Now installing Lavalink")
    assert not os.system(install_lavalink_command), "Failed to install Lavalink"
    print("Writing default lavalink config")
    with open("application.yml", "w") as f:
        f.write(default_lavalink_config)
    # now need to run lavalink as service
    print("Wrote default lavalink config. Lavalink installation is finally done")


def run_lavalink():
    print("Writing lavalink service file")
    with open("/etc/systemd/system/lavalink.service", "w") as f:
        f.write(install_lavalink_service)
    print(
        "Done writing lavalink service file. Now reloading systemd and enabling lavalink service"
    )
    assert not os.system("systemctl daemon-reload"), "Failed to reload systemd"
    print("Done reloading systemd. Now enabling lavalink service")
    assert not os.system(
        "systemctl enable lavalink"
    ), "Failed to enable lavalink service"
    print("Done enabling lavalink service. Now starting lavalink service")
    assert not os.system("systemctl start lavalink"), "Failed to start lavalink service"
    print("Successfully started lavalink service")


if __name__ == "__main__":
    check_env_vars()
    check_lavalink()
