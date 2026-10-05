# Glance Docker Dashboard

A live Docker dashboard for [Glance](https://github.com/glanceapp/glance) and compatible Glance forks.

This project combines a Glance `custom-api` widget with a small Python helper and browser-side JavaScript to provide live Docker stack/container status, richer service information, optional metrics from common self-hosted applications, and optional container update/redeploy controls through Dockhand.

It runs alongside Glance and does **not** require modifying or rebuilding Glance itself.

---

## Features

- Docker stack and container status
- Live browser-side updates without reloading the entire Glance page
- Stack grouping and friendly display names
- Custom icons and portal links
- Rich service-specific status cards
- Optional metrics from common self-hosted applications
- Optional Dockhand integration for image update checks
- One-click redeploy of supported Docker stacks
- Configurable browser-side helper URL for reverse proxies and HTTPS deployments
- Works with standard Glance and compatible Glance forks

Optional integrations include services such as:

- Dockhand
- qBittorrent
- Sonarr
- Radarr
- Prowlarr
- Bazarr
- Plex
- Jellyfin
- Tautulli
- Immich
- Tdarr
- Netdata
- Beszel
- Scrutiny
- Gatus
- Home Assistant
- Paperless-ngx
- Uptime Kuma
- Tailscale
- and others

You only need to configure integrations you actually use.

---

## How it works

The dashboard has two paths to the helper service.

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
      |
      +---- optional Dockhand API


Browser
      |
      | http(s)://GLANCE-HOST:30083/docker-stacks
      v
docker-data helper
```

Glance uses `docker-data` for the initial `custom-api` render.

After the page loads, the browser-side JavaScript uses the same helper for live data and supported management actions.

The browser-side helper endpoints include:

```text
/docker-stacks
/check-updates
/redeploy-stack
```

---

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

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/lumbu23/glance-docker-dashboard.git
cd glance-docker-dashboard
```

---

## 2. Create your local configuration

Create `.env`:

```bash
cp .env.example .env
```

Create your display overrides:

```bash
cp config/docker-data/overrides.example.yml \
   config/docker-data/overrides.yml
```

Edit both files for your environment.

Most service integrations are optional.

---

## 3. Docker networking

The supplied Glance widget calls:

```text
http://docker-data:8080/docker-stacks
```

That request is made **from the Glance container**, not from the browser.

Therefore Glance and `docker-data` must share a Docker network.

For example:

```yaml
networks:
  glance:
    external: true
```

Attach the helper:

```yaml
services:
  docker-data:
    networks:
      - glance
```

Your Glance container must join the same network.

If your Glance network already exists under another name, use that network instead.

### Optional application networks

If `docker-data` talks to applications using Docker DNS names such as:

```text
http://sonarr:8989
http://radarr:7878
http://jellyfin:8096
http://dockhand:3000
```

it must also share an appropriate Docker network with those containers.

Alternatively, configure URLs that are otherwise reachable from inside the `docker-data` container.

---

## 4. Start docker-data

Start the helper:

```bash
docker compose up -d
```

Check its logs:

```bash
docker compose logs -f docker-data
```

Test the published endpoint:

```bash
curl http://127.0.0.1:30083/docker-stacks
```

You should receive JSON rather than a connection error.

---

# Add the widget to Glance

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

Then include it in the desired column or widget list:

```yaml
widgets:
  - $include: widgets/docker.yml
```

The supplied widget uses:

```yaml
- type: custom-api
  title: Docker
  cache: 1s
  url: http://docker-data:8080/docker-stacks
```

If your helper uses a different Docker hostname or internal port, change that URL accordingly.

---

# Install the JavaScript assets

Copy these files into the assets directory served by Glance:

```text
assets/live-widgets.js
assets/docker-live.js
assets/docker-portals.js
```

A typical Glance deployment mounts an assets directory:

```yaml
volumes:
  - ./assets:/app/assets
```

and configures:

```yaml
server:
  assets-path: /app/assets
```

Load the JavaScript through Glance's `document.head`.

The order matters: `live-widgets.js` must load before `docker-live.js`.

```yaml
document:
  head: |
    <script src="/assets/live-widgets.js"></script>
    <script src="/assets/docker-live.js"></script>
    <script src="/assets/docker-portals.js"></script>
```

Restart Glance after installing the files.

---

# Browser-side helper URL

The initial custom widget request and the live browser requests use different network paths.

The Glance container uses:

```text
http://docker-data:8080
```

The browser cannot normally resolve Docker-only hostnames such as `docker-data`.

By default, `docker-live.js` therefore uses the hostname and protocol of the current Glance page with port `30083`.

For example, if Glance is opened at:

```text
http://192.168.1.10:8080
```

the live Docker helper is expected at:

```text
http://192.168.1.10:30083
```

The browser will call:

```text
http://192.168.1.10:30083/docker-stacks
```

and supported management actions use:

```text
http://192.168.1.10:30083/check-updates
http://192.168.1.10:30083/redeploy-stack
```

---

## Custom helper port

The default browser-side port is:

```text
30083
```

You can override it before loading `docker-live.js`:

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

---

## Custom helper URL

You can instead provide a complete helper base URL:

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

When `GLANCE_DOCKER_DATA_URL` is set, the dashboard uses it for:

```text
/docker-stacks
/check-updates
/redeploy-stack
```

For example:

```text
https://glance.example.com/docker-data/docker-stacks
https://glance.example.com/docker-data/check-updates
https://glance.example.com/docker-data/redeploy-stack
```

This is particularly useful when Glance itself is served through HTTPS.

A browser displaying an HTTPS page will normally reject direct requests to an insecure HTTP helper as mixed content.

---

# Optional service integrations

The core dashboard can obtain Docker state directly.

Additional information can be collected from supported applications when their URLs and credentials are configured.

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

See `.env.example` for the available settings.

If Docker hostnames such as `sonarr`, `radarr`, or `jellyfin` are used, `docker-data` must be able to resolve and reach those containers.

---

# Dockhand integration

Dockhand is optional.

The main Docker dashboard can still display Docker state without it.

Configuring Dockhand adds the update-management capabilities used by the dashboard.

These include:

- requesting a container image update check
- exposing update availability through the Docker dashboard state
- triggering supported stack redeploys
- refreshing the UI while Docker state changes after an action

## Configure Dockhand

Add the following to `.env`:

```env
DOCKHAND_URL=http://dockhand:3000
DOCKHAND_ENV_ID=1
```

`DOCKHAND_URL` must be reachable from the `docker-data` container.

If `dockhand` is a Docker hostname, Dockhand and `docker-data` need a shared Docker network.

For example:

```yaml
services:
  docker-data:
    networks:
      - management

networks:
  management:
    external: true
```

Dockhand must also be attached to `management`.

If Dockhand is reachable through another hostname or IP, that URL can be used instead.

---

# Container update checking

The Docker dashboard provides a helper endpoint at:

```text
/check-updates
```

When an update check is initiated, the browser sends the request to `docker-data`.

The request path is:

```text
Browser
   |
   | /check-updates
   v
docker-data
   |
   v
Dockhand
   |
   v
container image update check
```

The dashboard then continues polling the normal Docker state endpoint:

```text
/docker-stacks
```

so the displayed state can reflect the results of the check.

The browser does not need to contact Dockhand directly.

Dockhand credentials and connectivity stay on the server-side helper.

---

# Redeploying containers

Supported stacks can be redeployed through the dashboard.

The browser sends the action to:

```text
/redeploy-stack
```

The flow is:

```text
Browser
   |
   | /redeploy-stack
   v
docker-data
   |
   v
Dockhand
   |
   v
Docker stack redeploy
```

After the redeploy request, the normal live polling system refreshes the dashboard so changes in container state can be shown without requiring a full Glance page reload.

---

## Redeploy exclusions

Some management/infrastructure stacks should not be redeployed from the dashboard because they may be responsible for the dashboard or its own management path.

The default browser-side exclusion list includes:

```text
dockhand
ix-dockhand
glance
glance-dashboard
docker-data
glance-docker-data
```

The exclusion list is defined in:

```text
assets/docker-live.js
```

If your stack names differ, adjust the list to match your installation.

---

# Update architecture

A typical image update flow looks like this:

```text
User requests update check
          |
          v
docker-live.js
          |
          | POST /check-updates
          v
docker-data
          |
          v
Dockhand
          |
          v
image update scan
          |
          v
/docker-stacks polling
          |
          v
updated dashboard state
```

A redeploy follows:

```text
User requests redeploy
          |
          v
docker-live.js
          |
          | POST /redeploy-stack
          v
docker-data
          |
          v
Dockhand
          |
          v
Docker
          |
          | pull / recreate / restart as applicable
          v
/docker-stacks polling
          |
          v
updated dashboard state
```

The dashboard remains driven by the state reported by the backend rather than assuming that a requested Docker action completed immediately.

---

# Dockhand environment variables

The relevant `.env` section is:

```env
# -------------------------------------------------------------------
# Dockhand — optional container update/redeploy support
# -------------------------------------------------------------------

# URL reachable from docker-data.
DOCKHAND_URL=http://dockhand:3000

# Dockhand environment containing the Docker stacks being managed.
DOCKHAND_ENV_ID=1
```

If you do not use Dockhand:

```env
DOCKHAND_URL=
```

The core dashboard can still operate, but Dockhand-dependent update and redeploy functionality will not be available.

---

# Overrides

`config/docker-data/overrides.yml` controls how Docker stacks are presented.

Start with:

```bash
cp config/docker-data/overrides.example.yml \
   config/docker-data/overrides.yml
```

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

  radarr:
    port: 7878
    path: /
```

Keys normally correspond to Docker stack or container names.

Remove example entries that do not apply to your environment and add your own as needed.

---

# Portal links

`docker-portals.js` can turn supported Docker cards into links to their associated applications.

Portal information can be configured in `overrides.yml`.

For example:

```yaml
portals:
  sonarr:
    port: 8989
    path: /

  plex:
    port: 32400
    path: /web
```

The portal logic uses the current Glance host as the basis for local service URLs.

This works well for services exposed on different ports of the same host.

---

# Example `.env`

A minimal setup may only need:

```env
TZ=America/New_York
```

A larger setup might look like:

```env
TZ=America/New_York

DOCKHAND_URL=http://dockhand:3000
DOCKHAND_ENV_ID=1

SONARR_URL=http://sonarr:8989
SONARR_API_KEY=

RADARR_URL=http://radarr:7878
RADARR_API_KEY=

PROWLARR_URL=http://prowlarr:9696
PROWLARR_API_KEY=

BAZARR_URL=http://bazarr:6767
BAZARR_API_KEY=

JELLYFIN_URL=http://jellyfin:8096
JELLYFIN_API_KEY=

TAUTULLI_URL=http://tautulli:8181
TAUTULLI_API_KEY=

IMMICH_URL=http://immich-server:2283
IMMICH_API_KEY=
IMMICH_LIBRARY_ID=

QBIT_URL=http://qbittorrent:8080
QBIT_API_KEY=
```

Do not commit your real `.env`.

---

# Security

## Docker socket

The helper mounts:

```text
/var/run/docker.sock
```

Access to the Docker socket should be considered privileged access to the Docker host.

The Compose example uses:

```yaml
- /var/run/docker.sock:/var/run/docker.sock:ro
```

but the `:ro` bind-mount flag does **not** make the Docker API itself read-only.

The Docker socket is an API endpoint, not merely a normal file.

Treat `docker-data` as a privileged service.

---

## Management endpoints

The following endpoints perform or initiate management actions:

```text
/check-updates
/redeploy-stack
```

Do not expose them as an unauthenticated public API.

Keep the helper on:

- a trusted LAN
- a VPN
- or behind an authenticated reverse proxy

The helper's request checks should be considered additional safeguards, not a substitute for proper network access controls.

---

## API credentials

Optional integrations may require:

- API keys
- access tokens
- usernames
- passwords

Store these values in `.env`.

Do not commit `.env` to Git.

The repository's `.env.example` should contain variable names and examples only, never real credentials.

---

# Troubleshooting

## Widget cannot connect to docker-data

The initial widget request is made from the Glance container.

Test from Glance:

```bash
docker exec glance wget -qO- \
  http://docker-data:8080/docker-stacks
```

If it fails, verify that Glance and `docker-data` share a Docker network.

---

## Initial widget works but live updates fail

The initial render and live updates use different network paths.

The initial request is:

```text
Glance -> docker-data:8080
```

while live updates are:

```text
Browser -> GLANCE-HOST:30083
```

From a computer displaying Glance, verify that this URL is reachable:

```text
http://YOUR-GLANCE-HOST:30083/docker-stacks
```

---

## Update checking does not work

Verify that Dockhand is configured:

```env
DOCKHAND_URL=http://dockhand:3000
DOCKHAND_ENV_ID=1
```

Then verify `docker-data` can reach Dockhand.

If both containers use Docker hostnames, make sure they share a network.

Check helper logs:

```bash
docker compose logs -f docker-data
```

---

## Redeploy controls do not work

First verify that the stack is not intentionally excluded.

Default exclusions include:

```text
dockhand
ix-dockhand
glance
glance-dashboard
docker-data
glance-docker-data
```

Then verify Dockhand connectivity and inspect:

```bash
docker compose logs -f docker-data
```

---

## Glance uses HTTPS but live updates fail

An HTTPS page will normally block requests to an HTTP helper.

Expose `docker-data` through HTTPS and configure:

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

All live helper requests will then use that HTTPS base URL.

---

## Optional service metrics are unavailable

Verify that:

1. the application's URL is configured,
2. the required API credentials are configured,
3. the URL is reachable from `docker-data`,
4. the containers share a Docker network if Docker DNS names are used.

---

## Inspect helper logs

```bash
docker compose logs -f docker-data
```

---

# Compatibility

This project is intended for Glance and compatible Glance forks supporting:

- `custom-api` widgets
- `$include`
- custom assets
- `document.head`

The integration runs externally and does not require changes to the Glance source code.

---

# Updating Glance Docker Dashboard

Pull the latest project changes:

```bash
git pull
```

Rebuild the helper if `docker-data` changed:

```bash
docker compose build docker-data
docker compose up -d docker-data
```

If JavaScript assets changed, copy or update them in the assets directory used by your Glance installation and restart Glance if necessary.

If `docker.yml` changed, update the copy in your Glance configuration.

---

# License

This project is distributed under the license included in the repository.

---

# Disclaimer

This is a community project and is not affiliated with or maintained by the Glance project.

Glance is developed separately by the Glance project and its contributors.
