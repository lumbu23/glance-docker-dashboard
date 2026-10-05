# Glance Docker Dashboard

A live Docker dashboard for [Glance](https://github.com/glanceapp/glance) and compatible Glance forks.

This project combines a Glance `custom-api` widget with a small Python helper and browser-side JavaScript to provide live Docker stack/container status and optional metrics from common self-hosted applications.

It does not require a modified Glance binary.

## Features

- Docker stack and container status
- Live updates without reloading the entire Glance page
- Stack grouping and friendly display names
- Custom icons and portal links
- Update checks and supported stack redeploy actions
- Optional service-specific metrics
- Support for many common self-hosted applications

Optional integrations include services such as qBittorrent, Sonarr, Radarr, Prowlarr, Bazarr, Plex, Jellyfin, Tautulli, Immich, Tdarr, Netdata, Beszel, Scrutiny, Dockhand, Gatus, Home Assistant, Paperless-ngx, Uptime Kuma and Tailscale.

Only configure integrations you actually use.

## How it works

There are two paths to the helper service:

```text
Glance container
      |
      | http://docker-data:8080/docker-stacks
      v
docker-data helper
      |
      +---- Docker socket
      |
      +---- optional service APIs


Browser
      |
      | http(s)://GLANCE-HOST:30083/docker-stacks
      v
docker-data helper
```

Glance uses the helper for the initial `custom-api` render.

The browser-side JavaScript then talks to the same helper for live status, update checks and supported Docker actions.

## Repository layout

```text
.
├── .env.example
├── .gitignore
├── README.md
├── assets/
│   ├── docker-live.js
│   ├── docker-portals.js
│   └── live-widgets.js
├── compose.yml
├── config/
│   ├── docker-data/
│   │   └── overrides.example.yml
│   └── widgets/
│       └── docker.yml
└── docker-data/
    ├── Dockerfile
    └── app.py
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/lumbu23/glance-docker-dashboard.git
cd glance-docker-dashboard
```

### 2. Create your configuration

```bash
cp .env.example .env

cp config/docker-data/overrides.example.yml \
   config/docker-data/overrides.yml
```

Edit `.env` and `config/docker-data/overrides.yml` for your environment.

The integrations are optional.

## Docker networking

The Glance container must be able to resolve:

```text
docker-data
```

because the supplied widget calls:

```text
http://docker-data:8080/docker-stacks
```

Attach Glance and `docker-data` to the same Docker network.

For example:

```yaml
networks:
  glance:
    external: true
```

and:

```yaml
services:
  docker-data:
    networks:
      - glance
```

Your Glance container must join the same network.

If optional services use Docker hostnames such as:

```text
http://sonarr:8989
http://radarr:7878
http://jellyfin:8096
```

the helper must also share an appropriate Docker network with those containers.

## Start the helper

```bash
docker compose up -d
```

Check the logs:

```bash
docker compose logs -f docker-data
```

Test the helper:

```bash
curl http://127.0.0.1:30083/docker-stacks
```

You should receive JSON.

## Add the widget to Glance

Copy:

```text
config/widgets/docker.yml
```

into your Glance configuration.

For example:

```text
glance/
└── config/
    ├── glance.yml
    └── widgets/
        └── docker.yml
```

Then include it in the desired column:

```yaml
widgets:
  - $include: widgets/docker.yml
```

## Install the JavaScript assets

Copy these files into the assets directory served by Glance:

```text
assets/live-widgets.js
assets/docker-live.js
assets/docker-portals.js
```

A typical Glance setup mounts an assets directory:

```yaml
volumes:
  - ./assets:/app/assets
```

and configures:

```yaml
server:
  assets-path: /app/assets
```

Load the JavaScript through `document.head`.

`live-widgets.js` must load before `docker-live.js`.

```yaml
document:
  head: |
    <script src="/assets/live-widgets.js"></script>
    <script src="/assets/docker-live.js"></script>
    <script src="/assets/docker-portals.js"></script>
```

Restart Glance after installing the assets.

## Browser-side helper URL

By default, the live JavaScript uses the hostname and protocol of the current Glance page with port `30083`.

For example:

```text
Glance:
http://192.168.1.10:8080

docker-data:
http://192.168.1.10:30083
```

### Custom port

Set the port before loading `docker-live.js`:

```yaml
document:
  head: |
    <script>
      window.GLANCE_DOCKER_DATA_PORT = 30083;
    </script>
    <script src="/assets/live-widgets.js"></script>
    <script src="/assets/docker-live.js"></script>
    <script src="/assets/docker-portals.js"></script>
```

### Custom helper URL

A complete helper base URL can also be supplied:

```yaml
document:
  head: |
    <script>
      window.GLANCE_DOCKER_DATA_URL =
        "https://glance.example.com/docker-data";
    </script>

    <script src="/assets/live-widgets.js"></script>
    <script src="/assets/docker-live.js"></script>
    <script src="/assets/docker-portals.js"></script>
```

The following requests will all use that base URL:

```text
/docker-stacks
/check-updates
/redeploy-stack
```

Using a custom HTTPS URL is recommended when Glance itself is behind HTTPS.

## Optional integrations

Examples:

```env
SONARR_URL=http://sonarr:8989
SONARR_API_KEY=

RADARR_URL=http://radarr:7878
RADARR_API_KEY=

JELLYFIN_URL=http://jellyfin:8096
JELLYFIN_API_KEY=

QBIT_URL=http://qbittorrent:8080
QBIT_API_KEY=
```

See `.env.example` for the complete list.

## Overrides

`config/docker-data/overrides.yml` controls presentation.

Example:

```yaml
groups:
  qbittorrent: Downloads
  sonarr: Downloads
  radarr: Downloads
  jellyfin: Media

names:
  qbittorrent: qBittorrent

icons:
  qbittorrent: qbittorrent
  jellyfin: jellyfin

portals:
  jellyfin:
    port: 8096
    path: /

  sonarr:
    port: 8989
    path: /
```

Keys normally correspond to Docker stack or container names.

## Security

### Docker socket

The helper connects to:

```text
/var/run/docker.sock
```

Docker socket access should be considered privileged access to the Docker host.

The `:ro` bind-mount flag does not make Docker API operations read-only.

Do not expose the helper directly to the public Internet.

Use a trusted LAN, VPN, or authenticated reverse proxy.

### Credentials

Optional integrations may require API keys, tokens, usernames or passwords.

Keep these values in `.env`.

Do not commit `.env` to Git.

## Troubleshooting

### Widget cannot connect to docker-data

The initial widget request comes from Glance itself.

Test from the Glance container:

```bash
docker exec glance wget -qO- \
  http://docker-data:8080/docker-stacks
```

If that fails, make sure Glance and `docker-data` share a Docker network.

### Initial render works but live updates do not

The initial render and live updates use different network paths.

From a browser on the same network, verify:

```text
http://YOUR-GLANCE-HOST:30083/docker-stacks
```

is reachable.

### HTTPS Glance installation

Use:

```text
window.GLANCE_DOCKER_DATA_URL
```

and expose the helper through HTTPS.

Otherwise browsers may block mixed-content HTTP requests.

### Optional service metrics are unavailable

Verify that the relevant URL is reachable from inside the `docker-data` container and that the required credentials are configured.

### Helper logs

```bash
docker compose logs -f docker-data
```

## Compatibility

This project is designed for Glance and compatible Glance forks supporting:

- `custom-api`
- `$include`
- custom assets
- `document.head`

It is an external integration and does not require modifications to Glance itself.

## Disclaimer

This is a community project and is not affiliated with or maintained by the Glance project.
