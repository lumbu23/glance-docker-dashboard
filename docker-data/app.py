import concurrent.futures
import copy
import http.client
import json
import os
import re
import socket
import threading
import time
import urllib.parse
import urllib.request
import yaml
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class DualStackThreadingHTTPServer(ThreadingHTTPServer):
    """IPv6 listener that also accepts IPv4-mapped connections."""
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(
            socket.IPPROTO_IPV6,
            socket.IPV6_V6ONLY,
            0,
        )
        super().server_bind()




# =============================================================================
# CONFIGURATION
# =============================================================================

DOCKER_SOCKET = "/var/run/docker.sock"

HA_URL = os.environ.get(
    "HA_URL",
    "",
).rstrip("/")

HA_TOKEN = os.environ.get(
    "HA_TOKEN",
    "",
)

HOME_METRICS_TTL = 60

NETDATA_URL = os.environ.get(
    "NETDATA_URL",
    "",
).rstrip("/")

TRUENAS_METRICS_TTL = 12

truenas_metrics_lock = threading.Lock()
truenas_metrics_refresh_lock = threading.Lock()

truenas_metrics_cache = {
    "updated": 0,
    "data": None,
    "last_error": None,
}

DOCKHAND_URL = os.environ.get(
    "DOCKHAND_URL",
    "",
).rstrip("/")

DOCKHAND_ENV_ID = os.environ.get(
    "DOCKHAND_ENV_ID",
    "1",
)

OVERRIDES_FILE = os.environ.get(
    "OVERRIDES_FILE",
    "/config/overrides.yml",
)

SELFHST_PROJECTS_URL = (
    "https://raw.githubusercontent.com/"
    "rocketnova/selfhst-apps/"
    "refs/heads/main/data/projects.json"
)

SELFHST_ICON_BASE = (
    "https://cdn.jsdelivr.net/gh/"
    "selfhst/icons/png"
)

DASHBOARD_ICON_BASE = (
    "https://cdn.jsdelivr.net/gh/"
    "homarr-labs/dashboard-icons/png"
)

CATALOG_TTL = 12 * 60 * 60


# =============================================================================
# GROUPS
# =============================================================================

GROUP_ORDER = [
    "Media",
    "Downloads",
    "Monitoring",
    "Infrastructure",
    "Tools",
    "Other",
]


MEDIA_TAGS = {
    "media streaming",
    "movies",
    "music",
    "music streaming",
    "television",
    "photos",
    "videos",
    "video surveillance",
    "live streaming",
    "audiobook",
    "podcasts",
    "radio",
    "subtitles",
    "recording",
    "image sharing",
}

DOWNLOAD_TAGS = {
    "*arr",
    "downloads",
    "requests",
    "file transfer and sync",
    "file sharing",
    "usenet",
    "torrents",
}

MONITORING_TAGS = {
    "monitoring",
    "observability",
    "uptime",
    "logs",
    "statistics",
    "visualization",
    "analytics",
    "web analytics",
    "speed test",
}

INFRA_TAGS = {
    "docker",
    "server management",
    "networking",
    "vpn",
    "reverse proxy",
    "web server",
    "dns",
    "firewall",
    "authentication",
    "identity management",
    "remote access",
    "cloud storage",
    "object storage",
    "backups",
    "database",
    "relational database",
    "in-memory cache",
    "home automation",
    "smart home",
    "internet of things",
}


# =============================================================================
# CACHES
# =============================================================================

catalog_lock = threading.Lock()

catalog_cache = {
    "updated": 0,
    "projects": [],
    "index": {},
    "error": None,
}


overrides_lock = threading.Lock()

overrides_cache = {
    "mtime": None,
    "groups": {},
    "names": {},
    "icons": {},
    "portals": {},
    "order": {},
    "error": None,
}


# =============================================================================
# SERVICE METRICS
# =============================================================================

QBIT_URL = os.environ.get("QBIT_URL", "").rstrip("/")
QBIT_API_KEY = os.environ.get("QBIT_API_KEY", "")

SONARR_URL = os.environ.get("SONARR_URL", "").rstrip("/")
SONARR_API_KEY = os.environ.get("SONARR_API_KEY", "")

RADARR_URL = os.environ.get("RADARR_URL", "").rstrip("/")
RADARR_API_KEY = os.environ.get("RADARR_API_KEY", "")

TAUTULLI_URL = os.environ.get("TAUTULLI_URL", "").rstrip("/")
TAUTULLI_API_KEY = os.environ.get("TAUTULLI_API_KEY", "")

SPORTARR_URL = os.environ.get("SPORTARR_URL", "").rstrip("/")
SPORTARR_API_KEY = os.environ.get("SPORTARR_API_KEY", "")

PEANUT_URL = os.environ.get("PEANUT_URL", "").rstrip("/")
PEANUT_USERNAME = os.environ.get("PEANUT_USERNAME", "")
PEANUT_PASSWORD = os.environ.get("PEANUT_PASSWORD", "")
TAILSCALE_SOCKET = os.environ.get(
    "TAILSCALE_SOCKET",
    "/run/tailscale/tailscaled.sock",
)

SCRUTINY_URL = os.environ.get(
    "SCRUTINY_URL",
    "",
).rstrip("/")

IMMICH_URL = os.environ.get(
    "IMMICH_URL",
    "",
).rstrip("/")
IMMICH_API_KEY = os.environ.get(
    "IMMICH_API_KEY",
    "",
)

JELLYFIN_URL = os.environ.get(
    "JELLYFIN_URL",
    "",
).rstrip("/")
JELLYFIN_API_KEY = os.environ.get(
    "JELLYFIN_API_KEY",
    "",
)

PROWLARR_URL = os.environ.get(
    "PROWLARR_URL",
    "",
).rstrip("/")
PROWLARR_API_KEY = os.environ.get(
    "PROWLARR_API_KEY",
    "",
)

BAZARR_URL = os.environ.get(
    "BAZARR_URL",
    "",
).rstrip("/")

BAZARR_API_KEY = os.environ.get(
    "BAZARR_API_KEY",
    "",
)


UPTIME_KUMA_URL = os.environ.get(
    "UPTIME_KUMA_URL",
    "",
).rstrip("/")

UPTIME_KUMA_SLUG = os.environ.get(
    "UPTIME_KUMA_SLUG",
    "",
)


GATUS_URL = os.environ.get(
    "GATUS_URL",
    "http://gatus:8080",
).rstrip("/")


TDARR_URL = os.environ.get(
    "TDARR_URL",
    "",
).rstrip("/")

DISPATCHARR_URL = os.environ.get(
    "DISPATCHARR_URL",
    "",
).rstrip("/")
DISPATCHARR_USERNAME = os.environ.get(
    "DISPATCHARR_USERNAME",
    "",
)
DISPATCHARR_PASSWORD = os.environ.get(
    "DISPATCHARR_PASSWORD",
    "",
)

STORAGE_HISTORY_URL = os.environ.get(
    "STORAGE_HISTORY_URL",
    "http://storage-history:8080",
).rstrip("/")


BESZEL_URL = os.environ.get(
    "BESZEL_URL",
    "",
).rstrip("/")

BESZEL_EMAIL = os.environ.get(
    "BESZEL_EMAIL",
    "",
)

BESZEL_PASSWORD = os.environ.get(
    "BESZEL_PASSWORD",
    "",
)

BESZEL_SYSTEM_ID = os.environ.get(
    "BESZEL_SYSTEM_ID",
    "",
)


PAPERLESS_URL = os.environ.get(
    "PAPERLESS_URL",
    "",
).rstrip("/")

PAPERLESS_API_TOKEN = os.environ.get(
    "PAPERLESS_API_TOKEN",
    "",
)

SUBSCRIBARR_URL = os.environ.get(
    "SUBSCRIBARR_URL",
    "",
).rstrip("/")

SUBSCRIBARR_API_KEY = os.environ.get(
    "SUBSCRIBARR_API_KEY",
    "",
)


SERVICE_METRICS_TTL = 15

service_metrics_lock = threading.Lock()
service_metrics_refresh_lock = threading.Lock()

def api_json(url, headers=None, timeout=5):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "glance-docker-data/8.0",
            **(headers or {}),
        },
    )

    with urllib.request.urlopen(
        req,
        timeout=timeout,
    ) as response:
        return json.load(response)


class UnixSocketHTTPConnection(http.client.HTTPConnection):
    """HTTPConnection transported over a local Unix-domain socket."""

    def __init__(self, socket_path, host="localhost", timeout=5):
        super().__init__(host, timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        )
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


def unix_socket_json_request(
    socket_path,
    path,
    *,
    host="localhost",
    timeout=5,
    label="Unix socket API",
):
    conn = UnixSocketHTTPConnection(
        socket_path,
        host=host,
        timeout=timeout,
    )

    try:
        conn.request(
            "GET",
            path,
            headers={
                "Host": host,
                "Accept": "application/json",
            },
        )

        response = conn.getresponse()
        body = response.read()

        if response.status != 200:
            raise RuntimeError(
                f"{label} returned HTTP "
                f"{response.status} {response.reason}: "
                f"{body.decode(errors='replace')}"
            )

        return json.loads(body)

    finally:
        conn.close()


def mib_per_second(value):
    try:
        return round(float(value) / 1048576, 1)
    except Exception:
        return 0.0


def gib(value):
    try:
        return round(float(value) / 1073741824, 2)
    except Exception:
        return 0.0


def qbit_metrics():
    if not QBIT_URL:
        return {
            "available": False,
            "error": "QBIT_URL not configured",
        }

    headers = {}

    if QBIT_API_KEY:
        headers["Authorization"] = (
            f"Bearer {QBIT_API_KEY}"
        )

    transfer = api_json(
        f"{QBIT_URL}/api/v2/transfer/info",
        headers=headers,
    )

    torrents = api_json(
        f"{QBIT_URL}/api/v2/torrents/info"
        "?sort=upspeed&reverse=true",
        headers=headers,
    )

    downloading_states = {
        "downloading",
        "forcedDL",
        "metaDL",
        "allocating",
        "checkingDL",
        "stalledDL",
    }

    active_seed_states = {
        "uploading",
        "forcedUP",
    }

    idle_seed_states = {
        "stalledUP",
    }

    error_states = {
        "error",
        "missingFiles",
    }

    downloading = 0
    active_seeds = 0
    idle_seeds = 0
    errors = 0

    for torrent in torrents:
        state = torrent.get("state", "")

        if state in downloading_states:
            downloading += 1

        if state in active_seed_states:
            active_seeds += 1

        if state in idle_seed_states:
            idle_seeds += 1

        if state in error_states:
            errors += 1

    active = []

    for torrent in torrents:
        dl = int(torrent.get("dlspeed") or 0)
        up = int(torrent.get("upspeed") or 0)

        if dl + up <= 0:
            continue

        active.append({
            "name": torrent.get("name", ""),
            "download_mib": mib_per_second(dl),
            "upload_mib": mib_per_second(up),
        })

        if len(active) >= 3:
            break

    return {
        "available": True,
        "download_mib": mib_per_second(
            transfer.get("dl_info_speed", 0)
        ),
        "upload_mib": mib_per_second(
            transfer.get("up_info_speed", 0)
        ),
        "session_download_gib": gib(
            transfer.get("dl_info_data", 0)
        ),
        "session_upload_gib": gib(
            transfer.get("up_info_data", 0)
        ),
        "total": len(torrents),
        "downloading": downloading,
        "active_seeds": active_seeds,
        "idle_seeds": idle_seeds,
        "errors": errors,
        "healthy": errors == 0,
        "active": active,
    }


def arr_metrics(base_url, api_key):
    if not base_url:
        return {
            "available": False,
            "error": "URL not configured",
        }

    headers = {
        "X-Api-Key": api_key,
    }

    queue = api_json(
        f"{base_url}/api/v3/queue?page=1&pageSize=1",
        headers=headers,
    )

    health = api_json(
        f"{base_url}/api/v3/health",
        headers=headers,
    )

    missing = api_json(
        f"{base_url}/api/v3/wanted/missing?page=1&pageSize=1",
        headers=headers,
    )

    return {
        "available": True,
        "queue": int(
            queue.get("totalRecords", 0)
        ),
        "missing": int(
            missing.get("totalRecords", 0)
        ),
        "health_issues": len(health),
        "healthy": len(health) == 0,
    }




def parse_arr_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        )
    except Exception:
        return None


def arr_date_label(value):
    parsed = parse_arr_datetime(value)

    if not parsed:
        return ""

    return (
        f"{parsed.strftime('%a')} "
        f"{parsed.day}"
    )


def arr_calendar(
    base_url,
    api_key,
    include_series=False,
):
    now = datetime.now().astimezone()

    start = now.date().isoformat()

    end = (
        now
        + timedelta(days=7)
    ).date().isoformat()

    params = {
        "start": start,
        "end": end,
    }

    if include_series:
        params[
            "includeSeries"
        ] = "true"

    url = (
        f"{base_url}/api/v3/calendar?"
        + urllib.parse.urlencode(
            params
        )
    )

    return api_json(
        url,
        headers={
            "X-Api-Key": api_key,
        },
    )


def sonarr_metrics():
    result = arr_metrics(
        SONARR_URL,
        SONARR_API_KEY,
    )

    if not result.get(
        "available"
    ):
        return result

    calendar = arr_calendar(
        SONARR_URL,
        SONARR_API_KEY,
        include_series=True,
    )

    upcoming = []

    for item in calendar:
        if not item.get(
            "monitored",
            False,
        ):
            continue

        air_date_utc = item.get(
            "airDateUtc",
            "",
        )

        parsed = parse_arr_datetime(
            air_date_utc
        )

        air_date = item.get(
            "airDate",
            "",
        )

        if not parsed:
            continue

        series = (
            item.get("series")
            or {}
        )

        title = (
            series.get("title")
            or item.get("seriesTitle")
            or item.get("title")
            or ""
        )

        season = int(
            item.get(
                "seasonNumber",
                0,
            )
            or 0
        )

        episode = int(
            item.get(
                "episodeNumber",
                0,
            )
            or 0
        )

        upcoming.append({
            "timestamp":
                parsed.timestamp(),

            "date":
                arr_date_label(
                    air_date
                ),

            "title":
                title,

            "episode":
                f"S{season:02d}E{episode:02d}",
        })

    upcoming.sort(
        key=lambda item:
            item["timestamp"]
    )

    result["upcoming"] = (
        upcoming[:5]
    )

    return result


def radarr_metrics():
    result = arr_metrics(
        RADARR_URL,
        RADARR_API_KEY,
    )

    if not result.get(
        "available"
    ):
        return result

    calendar = arr_calendar(
        RADARR_URL,
        RADARR_API_KEY,
    )

    upcoming = []

    for item in calendar:
        if not item.get(
            "monitored",
            False,
        ):
            continue

        release_date = ""
        release_type = ""

        if item.get(
            "digitalRelease"
        ):
            release_date = item[
                "digitalRelease"
            ]
            release_type = "DIGITAL"

        elif item.get(
            "physicalRelease"
        ):
            release_date = item[
                "physicalRelease"
            ]
            release_type = "DISC"

        elif item.get(
            "inCinemas"
        ):
            release_date = item[
                "inCinemas"
            ]
            release_type = "CINEMA"

        parsed = parse_arr_datetime(
            release_date
        )

        if not parsed:
            continue

        upcoming.append({
            "timestamp":
                parsed.timestamp(),

            "date":
                arr_date_label(
                    release_date
                ),

            "title":
                item.get(
                    "title",
                    "",
                ),

            "release_type":
                release_type,
        })

    upcoming.sort(
        key=lambda item:
            item["timestamp"]
    )

    result["upcoming"] = (
        upcoming[:5]
    )

    return result


def sportarr_metrics():
    if not SPORTARR_URL:
        return {
            "available": False,
            "error": "SPORTARR_URL not configured",
        }

    if not SPORTARR_API_KEY:
        return {
            "available": False,
            "error": "SPORTARR_API_KEY not configured",
        }

    now = datetime.now(
        timezone.utc
    )

    start = now.date().isoformat()

    end = (
        now
        + timedelta(days=7)
    ).date().isoformat()

    params = {
        "start": start,
        "end": end,
        "includeSeries": "true",
    }

    calendar_url = (
        f"{SPORTARR_URL}/api/v3/calendar?"
        + urllib.parse.urlencode(
            params
        )
    )

    calendar = api_json(
        calendar_url,
        headers={
            "X-Api-Key":
                SPORTARR_API_KEY,
        },
    )

    upcoming = []

    for item in calendar:
        if not item.get(
            "monitored",
            False,
        ):
            continue

        event_date = (
            item.get("airDateUtc")
            or item.get("eventDate")
            or ""
        )

        parsed = parse_arr_datetime(
            event_date
        )

        if not parsed:
            continue

        title = (
            item.get("title")
            or ""
        )

        series = (
            item.get("series")
            or {}
        )

        # Sportarr versions expose slightly different metadata.
        # Use the richest available value and otherwise leave it blank.
        league = (
            item.get("leagueName")
            or item.get("league")
            or series.get("leagueName")
            or series.get("network")
            or ""
        )

        sport = (
            item.get("sport")
            or series.get("sport")
            or ""
        )

        upcoming.append({
            "timestamp":
                parsed.timestamp(),

            "date":
                arr_date_label(
                    event_date
                ),

            "title":
                title,

            "league":
                str(league),

            "sport":
                str(sport),
        })

    upcoming.sort(
        key=lambda item:
            item["timestamp"]
    )

    return {
        "available": True,
        "upcoming": upcoming[:6],
        "upcoming_count": len(upcoming),
    }




def peanut_runtime_text(seconds):
    try:
        seconds = int(float(seconds))
    except (TypeError, ValueError):
        return ""

    if seconds < 0:
        return ""

    minutes = seconds // 60
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}h {minutes:02d}m"

    return f"{minutes}m"


def peanut_status_text(status):
    flags = set(str(status or "").upper().split())

    if "FSD" in flags:
        return "SHUTDOWN"
    if "RB" in flags:
        return "REPLACE BATTERY"
    if "LB" in flags:
        return "LOW BATTERY"
    if "OVER" in flags:
        return "OVERLOAD"
    if "OB" in flags:
        return "ON BATTERY"
    if "OL" in flags:
        return "ONLINE"
    if "BYPASS" in flags:
        return "BYPASS"

    return str(status or "UNKNOWN").upper()


def peanut_status_level(status):
    flags = set(str(status or "").upper().split())

    if flags.intersection({"FSD", "LB", "RB", "OVER"}):
        return "critical"

    if flags.intersection({"OB", "BYPASS"}):
        return "warning"

    if "OL" in flags:
        return "ok"

    return "unknown"


def tailscale_localapi_json(path):
    return unix_socket_json_request(
        TAILSCALE_SOCKET,
        path,
        host="local-tailscaled.sock",
        timeout=5,
        label="Tailscale LocalAPI",
    )


def tailscale_metrics():
    result = {
        "available": False,
        "connected": False,
        "backend_state": "",
        "self_online": False,
        "hostname": "",
        "ipv4": "",
        "peers_total": 0,
        "peers_online": 0,
        "peers_active": 0,
        "status_text": "UNAVAILABLE",
        "status_level": "unknown",
    }

    if not TAILSCALE_SOCKET:
        return result

    try:
        data = tailscale_localapi_json(
            "/localapi/v0/status"
        )

        backend_state = str(
            data.get("BackendState") or ""
        )

        self_data = (
            data.get("Self") or {}
        )

        self_online = bool(
            self_data.get("Online")
        )

        peers = (
            data.get("Peer") or {}
        )

        if isinstance(peers, dict):
            peer_list = list(
                peers.values()
            )

        elif isinstance(peers, list):
            peer_list = peers

        else:
            peer_list = []

        tailscale_ips = (
            data.get("TailscaleIPs")
            or []
        )

        ipv4 = ""

        for ip in tailscale_ips:
            if (
                isinstance(ip, str)
                and "." in ip
            ):
                ipv4 = ip
                break

        peers_total = len(
            peer_list
        )

        peers_online = sum(
            1
            for peer in peer_list
            if (
                isinstance(peer, dict)
                and peer.get("Online")
                is True
            )
        )

        peers_active = sum(
            1
            for peer in peer_list
            if (
                isinstance(peer, dict)
                and peer.get("Active")
                is True
            )
        )

        connected = (
            backend_state == "Running"
            and self_online
        )

        if connected:
            status_text = "CONNECTED"
            status_level = "ok"

        elif backend_state in (
            "NeedsLogin",
            "NoState",
        ):
            status_text = "NEEDS LOGIN"
            status_level = "warning"

        elif backend_state == "Stopped":
            status_text = "STOPPED"
            status_level = "critical"

        else:
            status_text = (
                backend_state.upper()
                if backend_state
                else "OFFLINE"
            )
            status_level = "critical"

        result.update({
            "available": True,
            "connected": connected,
            "backend_state":
                backend_state,
            "self_online":
                self_online,
            "hostname":
                str(
                    self_data.get(
                        "HostName"
                    )
                    or ""
                ),
            "ipv4":
                ipv4,
            "peers_total":
                peers_total,
            "peers_online":
                peers_online,
            "peers_active":
                peers_active,
            "status_text":
                status_text,
            "status_level":
                status_level,
        })

    except Exception as exc:
        print(
            "[tailscale] metrics error: "
            f"{exc}",
            flush=True,
        )

    return result


def peanut_metrics():
    if not PEANUT_URL:
        return {
            "available": False,
            "error": "PEANUT_URL not configured",
        }

    if not PEANUT_USERNAME or not PEANUT_PASSWORD:
        return {
            "available": False,
            "error": "PeaNUT credentials not configured",
        }

    import base64

    credentials = (
        f"{PEANUT_USERNAME}:{PEANUT_PASSWORD}"
    ).encode("utf-8")

    auth = base64.b64encode(
        credentials
    ).decode("ascii")

    devices = api_json(
        f"{PEANUT_URL}/api/v1/devices",
        headers={
            "Authorization": f"Basic {auth}",
        },
    )

    if not isinstance(devices, list) or not devices:
        return {
            "available": False,
            "error": "No UPS devices returned",
        }

    ups = devices[0]

    status = str(
        ups.get("ups.status", "")
    )

    charge = ups.get(
        "battery.charge"
    )

    runtime = ups.get(
        "battery.runtime"
    )

    load_percent = ups.get(
        "ups.load"
    )

    nominal_watts = ups.get(
        "ups.realpower.nominal"
    )

    load_watts = None

    try:
        if (
            load_percent is not None
            and nominal_watts is not None
        ):
            load_watts = round(
                float(load_percent)
                * float(nominal_watts)
                / 100.0
            )
    except (TypeError, ValueError):
        load_watts = None

    return {
        "available": True,

        "status": status,
        "status_text":
            peanut_status_text(status),
        "status_level":
            peanut_status_level(status),

        "battery_charge":
            charge,

        "runtime_seconds":
            runtime,
        "runtime_text":
            peanut_runtime_text(runtime),

        "load_percent":
            load_percent,
        "load_watts":
            load_watts,

        "nominal_watts":
            nominal_watts,

        "input_voltage":
            ups.get("input.voltage"),

        "output_voltage":
            ups.get("output.voltage"),

        "battery_voltage":
            ups.get("battery.voltage"),

        "battery_warning":
            ups.get("battery.charge.warning"),

        "battery_low":
            ups.get("battery.charge.low"),

        "model":
            ups.get("ups.model")
            or ups.get("device.model")
            or "",
    }



def tautulli_metrics():
    if not TAUTULLI_URL:
        return {
            "available": False,
            "error": "TAUTULLI_URL not configured",
        }

    if not TAUTULLI_API_KEY:
        return {
            "available": False,
            "error": "TAUTULLI_API_KEY not configured",
        }

    url = (
        f"{TAUTULLI_URL}/api/v2"
        f"?apikey={TAUTULLI_API_KEY}"
        "&cmd=get_activity"
    )

    payload = api_json(
        url,
        timeout=5,
    )

    response = payload.get(
        "response",
        {},
    )

    if response.get("result") != "success":
        raise RuntimeError(
            response.get(
                "message",
                "Tautulli API request failed",
            )
        )

    data = response.get(
        "data",
        {},
    ) or {}

    sessions = data.get(
        "sessions",
        [],
    ) or []

    direct_play = 0
    direct_stream = 0
    transcode = 0

    active_streams = []

    for session in sessions:
        decision = str(
            session.get(
                "transcode_decision",
                "",
            )
        ).lower()

        if decision == "transcode":
            transcode += 1

        elif decision == "copy":
            direct_stream += 1

        elif decision == "direct play":
            direct_play += 1

        else:
            video_decision = str(
                session.get(
                    "video_decision",
                    "",
                )
            ).lower()

            audio_decision = str(
                session.get(
                    "audio_decision",
                    "",
                )
            ).lower()

            if (
                video_decision == "transcode"
                or audio_decision == "transcode"
            ):
                transcode += 1

            elif (
                video_decision == "copy"
                or audio_decision == "copy"
            ):
                direct_stream += 1

            else:
                direct_play += 1

        # ------------------------------------------------------------------
        # Human-readable playback method
        # ------------------------------------------------------------------

        if decision == "transcode":
            playback_method = "TRANSCODE"

        elif decision == "copy":
            playback_method = "DIRECT STREAM"

        elif decision == "direct play":
            playback_method = "DIRECT PLAY"

        else:
            video_decision = str(
                session.get(
                    "video_decision",
                    "",
                )
            ).lower()

            audio_decision = str(
                session.get(
                    "audio_decision",
                    "",
                )
            ).lower()

            if (
                video_decision == "transcode"
                or audio_decision == "transcode"
            ):
                playback_method = "TRANSCODE"

            elif (
                video_decision == "copy"
                or audio_decision == "copy"
            ):
                playback_method = "DIRECT STREAM"

            else:
                playback_method = "DIRECT PLAY"

        media_type = str(
            session.get(
                "media_type",
                "",
            )
        ).lower()

        title = (
            session.get("full_title")
            or session.get("title")
            or session.get("grandparent_title")
            or "Unknown"
        )

        series_title = (
            session.get("grandparent_title")
            or ""
        )

        episode_title = (
            session.get("title")
            or ""
        )

        season = session.get(
            "parent_media_index"
        )

        episode = session.get(
            "media_index"
        )

        episode_code = ""

        try:
            if (
                media_type == "episode"
                and season is not None
                and episode is not None
            ):
                episode_code = (
                    f"S{int(season):02d}"
                    f"E{int(episode):02d}"
                )
        except Exception:
            episode_code = ""

        if media_type == "episode":
            display_title = (
                series_title
                or title
            )

            subtitle = " · ".join(
                value
                for value in (
                    episode_code,
                    episode_title,
                )
                if value
            )

        else:
            display_title = title
            subtitle = ""

        user = (
            session.get("friendly_name")
            or session.get("user")
            or ""
        )

        try:
            stream_bandwidth_kbps = int(
                session.get(
                    "bandwidth",
                    0,
                )
                or session.get(
                    "stream_container_decision",
                    0,
                )
                or 0
            )
        except Exception:
            stream_bandwidth_kbps = 0

        active_streams.append({
            "title": display_title,
            "subtitle": subtitle,
            "user": user,
            "method": playback_method,
            "media_type": media_type,
            "bandwidth_mbps": round(
                stream_bandwidth_kbps / 1000.0,
                1,
            ),
        })

    try:
        total_bandwidth = int(
            data.get(
                "total_bandwidth",
                0,
            )
            or 0
        )
    except Exception:
        total_bandwidth = 0

    try:
        lan_bandwidth = int(
            data.get(
                "lan_bandwidth",
                0,
            )
            or 0
        )
    except Exception:
        lan_bandwidth = 0

    try:
        wan_bandwidth = int(
            data.get(
                "wan_bandwidth",
                0,
            )
            or 0
        )
    except Exception:
        wan_bandwidth = 0

    return {
        "available": True,
        "streams": len(sessions),
        "direct_play": direct_play,
        "direct_stream": direct_stream,
        "transcode": transcode,
        "active_streams": active_streams,
        "total_bandwidth_kbps": total_bandwidth,
        "lan_bandwidth_kbps": lan_bandwidth,
        "wan_bandwidth_kbps": wan_bandwidth,
    }




def scrutiny_metrics():
    if not SCRUTINY_URL:
        return {
            "available": False,
            "error": "SCRUTINY_URL not configured",
        }

    payload = api_json(
        f"{SCRUTINY_URL}/api/summary",
        timeout=8,
    )

    data = payload.get("data") or {}
    summary = data.get("summary") or {}

    drives = 0
    warnings = 0
    temperatures = []

    if isinstance(summary, dict):
        entries = summary.values()
    elif isinstance(summary, list):
        entries = summary
    else:
        entries = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        device = entry.get("device") or {}

        if device.get("archived"):
            continue

        drives += 1

        try:
            device_status = int(
                device.get("device_status") or 0
            )
        except Exception:
            device_status = 0

        if device_status != 0:
            warnings += 1

        smart = entry.get("smart") or {}

        try:
            temp = int(smart.get("temp"))
            temperatures.append(temp)
        except Exception:
            pass

    return {
        "available": True,
        "drives": drives,
        "warnings": warnings,
        "healthy": warnings == 0,
        "max_temp":
            max(temperatures)
            if temperatures
            else 0,
    }



beszel_auth_lock = threading.Lock()

beszel_auth_cache = {
    "token": "",
    "updated": 0,
}


def beszel_auth_token(force=False):
    with beszel_auth_lock:
        token = beszel_auth_cache["token"]
        updated = beszel_auth_cache["updated"]

        if (
            not force
            and token
            and time.time() - updated < 20 * 60
        ):
            return token

        if not BESZEL_URL:
            raise RuntimeError(
                "BESZEL_URL not configured"
            )

        if not BESZEL_EMAIL or not BESZEL_PASSWORD:
            raise RuntimeError(
                "Beszel credentials not configured"
            )

        body = json.dumps({
            "identity": BESZEL_EMAIL,
            "password": BESZEL_PASSWORD,
        }).encode("utf-8")

        request = urllib.request.Request(
            BESZEL_URL
            + "/api/collections/users/auth-with-password",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent":
                    "glance-docker-data/8.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=8,
        ) as response:
            payload = json.load(response)

        token = str(
            payload.get("token") or ""
        )

        if not token:
            raise RuntimeError(
                "Beszel login returned no token"
            )

        beszel_auth_cache["token"] = token
        beszel_auth_cache["updated"] = time.time()

        return token


def beszel_api(path):
    token = beszel_auth_token()

    try:
        return api_json(
            f"{BESZEL_URL}{path}",
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
            timeout=8,
        )

    except urllib.error.HTTPError as exc:
        if exc.code not in (401, 403):
            raise

        with beszel_auth_lock:
            beszel_auth_cache["token"] = ""
            beszel_auth_cache["updated"] = 0

        token = beszel_auth_token(
            force=True
        )

        return api_json(
            f"{BESZEL_URL}{path}",
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
            timeout=8,
        )


def beszel_uptime_text(value):
    try:
        seconds = max(
            0,
            int(float(value)),
        )
    except (TypeError, ValueError):
        return ""

    days, remainder = divmod(
        seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes = remainder // 60

    if days:
        return f"{days}d {hours}h"

    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def beszel_metric_text(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"


def beszel_alert_text(
    alert,
    info,
    system_status,
):
    name = str(
        alert.get("name")
        or "Alert"
    ).strip()

    key = name.lower()

    labels = {
        "cpu": "CPU",
        "memory": "Memory",
        "ram": "Memory",
        "disk": "Disk",
        "status": "Status",
        "loadavg1": "Load 1m",
        "loadavg5": "Load 5m",
        "loadavg15": "Load 15m",
    }

    label = labels.get(
        key,
        name.replace("_", " ").title(),
    )

    if key == "status":
        text = (
            f"{label} "
            f"{system_status or 'down'}"
        )

    else:
        threshold = beszel_metric_text(
            alert.get("value")
        )

        if threshold:
            if key in {
                "cpu",
                "memory",
                "ram",
                "disk",
            }:
                text = (
                    f"{label} > {threshold}%"
                )
            else:
                text = (
                    f"{label} > {threshold}"
                )
        else:
            text = label

    try:
        minutes = int(
            float(alert.get("min") or 0)
        )
    except (TypeError, ValueError):
        minutes = 0

    if minutes > 0:
        text += f" · {minutes}m"

    return text


def beszel_metrics():
    if not BESZEL_URL:
        return {
            "available": False,
            "alerts_available": False,
            "error":
                "BESZEL_URL not configured",
        }

    if not BESZEL_SYSTEM_ID:
        return {
            "available": False,
            "alerts_available": False,
            "error":
                "BESZEL_SYSTEM_ID not configured",
        }

    system = beszel_api(
        "/api/collections/systems/records/"
        + urllib.parse.quote(
            BESZEL_SYSTEM_ID,
            safe="",
        )
    )

    info = system.get("info") or {}

    system_status = str(
        system.get("status") or ""
    ).lower()

    result = {
        "available": True,
        "alerts_available": True,
        "system_status": system_status,
        "healthy":
            system_status == "up",
        "cpu":
            float(info.get("cpu") or 0),
        "memory":
            float(info.get("mp") or 0),
        "uptime_seconds":
            int(float(info.get("u") or 0)),
        "uptime_text":
            beszel_uptime_text(
                info.get("u") or 0
            ),
        "alert_count": 0,
        "alerts": [],
    }

    try:
        payload = beszel_api(
            "/api/collections/alerts/records"
            "?page=1&perPage=200"
        )

        active = []

        for alert in (
            payload.get("items") or []
        ):
            if (
                str(
                    alert.get("system")
                    or ""
                )
                != BESZEL_SYSTEM_ID
            ):
                continue

            if not bool(
                alert.get("triggered")
            ):
                continue

            active.append({
                "name":
                    str(
                        alert.get("name")
                        or "Alert"
                    ),

                "text":
                    beszel_alert_text(
                        alert,
                        info,
                        system_status,
                    ),
            })

        result["alerts"] = active
        result["alert_count"] = len(
            active
        )

        result["healthy"] = (
            system_status == "up"
            and len(active) == 0
        )

    except Exception as exc:
        result[
            "alerts_available"
        ] = False

        result["alerts_error"] = (
            f"{type(exc).__name__}: {exc}"
        )

    return result


def immich_failed_jobs(payload):
    total = 0

    def walk(value, parent_key=""):
        nonlocal total

        if isinstance(value, dict):
            for key, child in value.items():
                key_lower = str(key).lower()

                if (
                    key_lower in {
                        "failed",
                        "failure",
                        "failures",
                    }
                    and isinstance(
                        child,
                        (int, float),
                    )
                ):
                    total += int(child)
                else:
                    walk(child, key_lower)

        elif isinstance(value, list):
            for child in value:
                walk(child, parent_key)

    walk(payload)
    return total


def immich_metrics():
    if not IMMICH_URL:
        return {
            "available": False,
            "error": "IMMICH_URL not configured",
        }

    if not IMMICH_API_KEY:
        return {
            "available": False,
            "error": "IMMICH_API_KEY not configured",
        }

    headers = {
        "x-api-key": IMMICH_API_KEY,
    }

    libraries = api_json(
        f"{IMMICH_URL}/api/libraries",
        headers=headers,
        timeout=8,
    )

    pictures_library = next(
        (
            library
            for library in libraries
            if str(
                library.get("name") or ""
            ).lower() == "pictures"
        ),
        None,
    )

    if not pictures_library:
        return {
            "available": False,
            "error": "Immich Pictures library not found",
        }

    library_id = pictures_library.get("id")

    stats = api_json(
        (
            f"{IMMICH_URL}/api/libraries/"
            f"{library_id}/statistics"
        ),
        headers=headers,
        timeout=8,
    )

    queues = api_json(
        f"{IMMICH_URL}/api/queues",
        headers=headers,
        timeout=8,
    )

    photos = int(stats.get("photos") or 0)
    videos = int(stats.get("videos") or 0)
    usage = int(stats.get("usage") or 0)

    failed_jobs = immich_failed_jobs(
        queues
    )

    return {
        "available": True,
        "photos": photos,
        "videos": videos,
        "assets": photos + videos,
        "usage": usage,
        "failed_jobs": failed_jobs,
        "healthy": failed_jobs == 0,
    }


def jellyfin_metrics():
    if not JELLYFIN_URL:
        return {
            "available": False,
            "error": "JELLYFIN_URL not configured",
        }

    if not JELLYFIN_API_KEY:
        return {
            "available": False,
            "error": "JELLYFIN_API_KEY not configured",
        }

    sessions = api_json(
        f"{JELLYFIN_URL}/Sessions",
        headers={
            "Authorization": (
                f'MediaBrowser Token="{JELLYFIN_API_KEY}", '
                'Client="Glance Docker Dashboard", '
                'Device="Glance Docker Dashboard", '
                'DeviceId="glance-docker-data", '
                'Version="1.0"'
            ),
        },
        timeout=8,
    )

    active = []
    transcodes = 0

    for session in sessions:
        item = (
            session.get("NowPlayingItem")
            or {}
        )

        if not item:
            continue

        transcoding = (
            session.get("TranscodingInfo")
            or {}
        )

        if transcoding:
            transcodes += 1
            method = "TRANSCODE"
        else:
            method = "DIRECT"

        media_type = str(
            item.get("Type") or ""
        ).lower()

        if media_type == "episode":
            series = (
                item.get("SeriesName")
                or item.get("Name")
                or "Unknown"
            )

            season = item.get(
                "ParentIndexNumber"
            )
            episode = item.get(
                "IndexNumber"
            )

            code = ""

            try:
                if (
                    season is not None
                    and episode is not None
                ):
                    code = (
                        f"S{int(season):02d}"
                        f"E{int(episode):02d}"
                    )
            except Exception:
                pass

            title = series

            subtitle = " · ".join(
                value
                for value in (
                    code,
                    item.get("Name") or "",
                )
                if value
            )

        else:
            title = (
                item.get("Name")
                or "Unknown"
            )
            subtitle = ""

        active.append({
            "title": title,
            "subtitle": subtitle,
            "user":
                session.get("UserName")
                or "",
            "method": method,
        })

    return {
        "available": True,
        "streams": len(active),
        "transcodes": transcodes,
        "active_streams": active[:2],
    }


def prowlarr_metrics():
    if not PROWLARR_URL:
        return {
            "available": False,
            "error": "PROWLARR_URL not configured",
        }

    if not PROWLARR_API_KEY:
        return {
            "available": False,
            "error": "PROWLARR_API_KEY not configured",
        }

    headers = {
        "X-Api-Key": PROWLARR_API_KEY,
    }

    indexers = api_json(
        f"{PROWLARR_URL}/api/v1/indexer",
        headers=headers,
        timeout=8,
    )

    status = api_json(
        f"{PROWLARR_URL}/api/v1/indexerstatus",
        headers=headers,
        timeout=8,
    )

    health = api_json(
        f"{PROWLARR_URL}/api/v1/health",
        headers=headers,
        timeout=8,
    )

    enabled = [
        item
        for item in indexers
        if item.get("enable", True)
    ]

    failed_ids = set()

    for item in status:
        indexer_id = item.get("indexerId")

        if indexer_id is not None:
            failed_ids.add(indexer_id)

    total = len(enabled)
    failed = len(failed_ids)
    healthy = max(0, total - failed)

    return {
        "available": True,
        "total": total,
        "healthy_count": healthy,
        "failed": failed,
        "health_issues": len(health),
        "healthy":
            failed == 0
            and len(health) == 0,
    }


def bazarr_metrics():
    if not BAZARR_URL:
        return {
            "available": False,
            "error": "BAZARR_URL not configured",
        }

    if not BAZARR_API_KEY:
        return {
            "available": False,
            "error": "BAZARR_API_KEY not configured",
        }

    headers = {
        "X-API-KEY": BAZARR_API_KEY,
    }

    status = api_json(
        f"{BAZARR_URL}/api/system/status",
        headers=headers,
        timeout=8,
    )

    episodes = api_json(
        f"{BAZARR_URL}/api/episodes/wanted"
        "?page=1&page_size=1",
        headers=headers,
        timeout=8,
    )

    movies = api_json(
        f"{BAZARR_URL}/api/movies/wanted"
        "?page=1&page_size=1",
        headers=headers,
        timeout=8,
    )

    providers = api_json(
        f"{BAZARR_URL}/api/providers",
        headers=headers,
        timeout=8,
    )

    status_data = (
        status.get("data", {})
        if isinstance(status, dict)
        else {}
    )

    provider_data = (
        providers.get("data", [])
        if isinstance(providers, dict)
        else []
    )

    if not isinstance(provider_data, list):
        provider_data = []

    provider_problems = []

    for provider in provider_data:
        if not isinstance(provider, dict):
            continue

        provider_status = str(
            provider.get("status") or ""
        )

        if provider_status.lower() != "good":
            provider_problems.append({
                "name":
                    str(provider.get("name") or ""),
                "status":
                    provider_status,
                "retry":
                    str(provider.get("retry") or ""),
            })

    wanted_episodes = int(
        episodes.get("total", 0) or 0
    ) if isinstance(episodes, dict) else 0

    wanted_movies = int(
        movies.get("total", 0) or 0
    ) if isinstance(movies, dict) else 0

    return {
        "available": True,
        "version":
            str(
                status_data.get(
                    "bazarr_version"
                ) or ""
            ),
        "wanted_episodes":
            wanted_episodes,
        "wanted_movies":
            wanted_movies,
        "providers":
            len(provider_data),
        "providers_good":
            max(
                0,
                len(provider_data)
                - len(provider_problems),
            ),
        "provider_issues":
            len(provider_problems),
        "provider_problems":
            provider_problems[:3],
        "healthy":
            len(provider_problems) == 0,
    }


def uptime_kuma_metrics():
    if not UPTIME_KUMA_URL:
        return {
            "available": False,
            "error": "UPTIME_KUMA_URL not configured",
        }

    if not UPTIME_KUMA_SLUG:
        return {
            "available": False,
            "error": "UPTIME_KUMA_SLUG not configured",
        }

    slug = urllib.parse.quote(
        UPTIME_KUMA_SLUG,
        safe="",
    )

    page = api_json(
        f"{UPTIME_KUMA_URL}/api/status-page/{slug}",
        timeout=8,
    )

    heartbeat_data = api_json(
        f"{UPTIME_KUMA_URL}/api/status-page/heartbeat/{slug}",
        timeout=8,
    )

    groups = (
        page.get("publicGroupList", [])
        if isinstance(page, dict)
        else []
    )

    heartbeat_list = (
        heartbeat_data.get("heartbeatList", {})
        if isinstance(heartbeat_data, dict)
        else {}
    )

    uptime_list = (
        heartbeat_data.get("uptimeList", {})
        if isinstance(heartbeat_data, dict)
        else {}
    )

    monitors = []

    for group in groups:
        if not isinstance(group, dict):
            continue

        for monitor in group.get("monitorList", []):
            if not isinstance(monitor, dict):
                continue

            monitor_id = monitor.get("id")

            if monitor_id is None:
                continue

            monitor_id_str = str(monitor_id)

            history = heartbeat_list.get(
                monitor_id_str,
                [],
            )

            latest = (
                history[-1]
                if isinstance(history, list)
                and history
                and isinstance(history[-1], dict)
                else {}
            )

            status = latest.get("status")

            try:
                status = int(status)
            except Exception:
                status = None

            uptime_value = uptime_list.get(
                f"{monitor_id_str}_24"
            )

            try:
                uptime_24h = float(uptime_value)
            except Exception:
                uptime_24h = None

            monitors.append({
                "id": monitor_id,
                "name": str(
                    monitor.get("name")
                    or f"Monitor {monitor_id}"
                ),
                "status": status,
                "ping": latest.get("ping"),
                "message": str(
                    latest.get("msg")
                    or ""
                ),
                "time": str(
                    latest.get("time")
                    or ""
                ),
                "uptime_24h": uptime_24h,
            })

    total = len(monitors)

    up = sum(
        1
        for monitor in monitors
        if monitor["status"] == 1
    )

    pending = sum(
        1
        for monitor in monitors
        if monitor["status"] == 2
    )

    down_monitors = [
        monitor
        for monitor in monitors
        if monitor["status"] == 0
    ]

    unknown_monitors = [
        monitor
        for monitor in monitors
        if monitor["status"] is None
    ]

    uptime_values = [
        monitor["uptime_24h"]
        for monitor in monitors
        if monitor["uptime_24h"] is not None
    ]

    if uptime_values:
        uptime_24h = round(
            (
                sum(uptime_values)
                / len(uptime_values)
            ) * 100,
            2,
        )
    else:
        uptime_24h = None

    problem_monitors = (
        down_monitors
        + unknown_monitors
    )

    problem_names = " · ".join(
        monitor["name"]
        for monitor in problem_monitors[:3]
    )

    return {
        "available": True,
        "total": total,
        "up": up,
        "down": len(down_monitors),
        "pending": pending,
        "unknown": len(unknown_monitors),
        "healthy":
            total > 0
            and len(down_monitors) == 0
            and len(unknown_monitors) == 0,
        "uptime_24h":
            uptime_24h
            if uptime_24h is not None
            else 0,
        "problem_names": problem_names,
        "problem_monitors": [
            {
                "name": monitor["name"],
                "status": monitor["status"],
                "message": monitor["message"],
            }
            for monitor in problem_monitors[:5]
        ],
    }


def gatus_duration_ms(value):
    try:
        # Gatus serializes Go time.Duration as nanoseconds.
        return round(float(value) / 1000000, 1)
    except (TypeError, ValueError):
        return None


def gatus_metrics():
    if not GATUS_URL:
        return {
            "available": False,
            "error": "GATUS_URL not configured",
        }

    endpoints = api_json(
        f"{GATUS_URL}/api/v1/endpoints/statuses",
        timeout=8,
    )

    if not isinstance(endpoints, list):
        return {
            "available": False,
            "error": "Unexpected Gatus API response",
        }

    parsed = []

    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            continue

        results = endpoint.get("results") or []

        latest = (
            results[-1]
            if isinstance(results, list)
            and results
            and isinstance(results[-1], dict)
            else {}
        )

        parsed.append({
            "name": str(
                endpoint.get("name")
                or endpoint.get("key")
                or "Endpoint"
            ),
            "success": latest.get("success") is True,
            "duration_ms": gatus_duration_ms(
                latest.get("duration")
            ),
        })

    total = len(parsed)
    up = sum(
        1 for endpoint in parsed
        if endpoint["success"]
    )
    down = total - up

    problems = [
        endpoint["name"]
        for endpoint in parsed
        if not endpoint["success"]
    ]

    response_samples = [
        endpoint
        for endpoint in parsed
        if endpoint["duration_ms"] is not None
    ]

    if response_samples:
        average_response_ms = round(
            sum(
                endpoint["duration_ms"]
                for endpoint in response_samples
            ) / len(response_samples),
            1,
        )

        slowest = max(
            response_samples,
            key=lambda endpoint:
                endpoint["duration_ms"],
        )

        slowest_name = slowest["name"]
        slowest_response_ms = slowest["duration_ms"]
    else:
        average_response_ms = 0
        slowest_name = ""
        slowest_response_ms = 0

    return {
        "available": True,
        "total": total,
        "up": up,
        "down": down,
        "healthy": total > 0 and down == 0,
        "problem_names": " · ".join(problems[:3]),
        "average_response_ms": average_response_ms,
        "slowest_name": slowest_name,
        "slowest_response_ms": slowest_response_ms,
    }


def tdarr_metrics():
    if not TDARR_URL:
        return {
            "available": False,
            "error": "TDARR_URL not configured",
        }

    status = api_json(
        f"{TDARR_URL}/api/v2/status",
        timeout=8,
    )

    nodes = api_json(
        f"{TDARR_URL}/api/v2/get-nodes",
        timeout=8,
    )

    node_count = 0
    active_nodes = 0
    workers = 0
    processing = 0
    queued = 0

    for node in nodes.values():
        if not isinstance(node, dict):
            continue

        node_count += 1

        if not node.get(
            "nodePaused",
            False,
        ):
            active_nodes += 1

        node_workers = (
            node.get("workers")
            or {}
        )

        if isinstance(
            node_workers,
            dict,
        ):
            workers += len(node_workers)

            for worker in node_workers.values():
                if not isinstance(
                    worker,
                    dict,
                ):
                    continue

                worker_status = str(
                    worker.get("status")
                    or worker.get("workerStatus")
                    or ""
                ).lower()

                if worker_status not in {
                    "",
                    "idle",
                    "paused",
                    "stopped",
                }:
                    processing += 1

        elif isinstance(
            node_workers,
            list,
        ):
            workers += len(node_workers)

            for worker in node_workers:
                if not isinstance(
                    worker,
                    dict,
                ):
                    continue

                worker_status = str(
                    worker.get("status")
                    or worker.get("workerStatus")
                    or ""
                ).lower()

                if worker_status not in {
                    "",
                    "idle",
                    "paused",
                    "stopped",
                }:
                    processing += 1

        queue_lengths = (
            node.get("queueLengths")
            or {}
        )

        if isinstance(
            queue_lengths,
            dict,
        ):
            for value in queue_lengths.values():
                try:
                    queued += int(value or 0)
                except Exception:
                    pass

        elif isinstance(
            queue_lengths,
            list,
        ):
            for value in queue_lengths:
                try:
                    queued += int(value or 0)
                except Exception:
                    pass

    return {
        "available": True,
        "status":
            str(status.get("status") or ""),
        "version":
            str(status.get("version") or ""),
        "nodes": node_count,
        "nodes_online": active_nodes,
        "workers": workers,
        "processing": processing,
        "queued": queued,
        "healthy":
            str(
                status.get("status") or ""
            ).lower() == "good",
    }


dispatcharr_token_lock = threading.Lock()
dispatcharr_token = {
    "access": "",
    "refresh": "",
    "updated": 0,
}


def dispatcharr_login():
    if (
        not DISPATCHARR_USERNAME
        or not DISPATCHARR_PASSWORD
    ):
        raise RuntimeError(
            "Dispatcharr credentials not configured"
        )

    body = json.dumps({
        "username": DISPATCHARR_USERNAME,
        "password": DISPATCHARR_PASSWORD,
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{DISPATCHARR_URL}/api/accounts/token/",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent":
                "glance-docker-data/8.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=8,
    ) as response:
        payload = json.load(response)

    access = payload.get("access") or ""

    if not access:
        raise RuntimeError(
            "Dispatcharr login returned no access token"
        )

    with dispatcharr_token_lock:
        dispatcharr_token["access"] = access
        dispatcharr_token["refresh"] = (
            payload.get("refresh") or ""
        )
        dispatcharr_token["updated"] = (
            time.time()
        )

    return access


def dispatcharr_access_token():
    with dispatcharr_token_lock:
        access = dispatcharr_token[
            "access"
        ]
        updated = dispatcharr_token[
            "updated"
        ]

    # Reuse the JWT instead of hitting Dispatcharr's login
    # endpoint every 15 seconds. Refresh conservatively.
    if (
        access
        and time.time() - updated < 15 * 60
    ):
        return access

    return dispatcharr_login()


def dispatcharr_api(path):
    token = dispatcharr_access_token()

    try:
        return api_json(
            f"{DISPATCHARR_URL}{path}",
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
            timeout=10,
        )

    except urllib.error.HTTPError as exc:
        if exc.code != 401:
            raise

        token = dispatcharr_login()

        return api_json(
            f"{DISPATCHARR_URL}{path}",
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
            timeout=10,
        )


def dispatcharr_metrics():
    if not DISPATCHARR_URL:
        return {
            "available": False,
            "error": "DISPATCHARR_URL not configured",
        }

    # Runtime connection statistics only.
    #
    # We intentionally do NOT query:
    #   /api/channels/channels/
    #
    # The dashboard does not need the configured channel
    # inventory count, and fetching the full channel list
    # is unnecessarily expensive.
    #
    # live.count:
    #   Number of active upstream/provider channel
    #   connections maintained by Dispatcharr.
    #
    # channel.client_count:
    #   Number of downstream/local clients consuming
    #   each active provider connection.
    stats = dispatcharr_api(
        "/proxy/stats/"
    )

    live = (
        stats.get("live")
        if isinstance(stats, dict)
        else {}
    ) or {}

    active_channels = (
        live.get("channels")
        if isinstance(live, dict)
        else []
    ) or []

    try:
        provider_connections = int(
            live.get("count") or 0
        )
    except Exception:
        provider_connections = len(
            active_channels
        )

    local_connections = 0

    for channel in active_channels:
        if not isinstance(channel, dict):
            continue

        try:
            local_connections += int(
                channel.get("client_count")
                or 0
            )
        except Exception:
            clients = (
                channel.get("clients")
                or []
            )

            if isinstance(clients, list):
                local_connections += len(
                    clients
                )

    return {
        "available": True,
        "local_connections":
            local_connections,
        "provider_connections":
            provider_connections,
        "active_channels":
            provider_connections,
    }

def paperless_metrics():
    if not PAPERLESS_URL:
        raise RuntimeError(
            "Paperless URL not configured"
        )

    if not PAPERLESS_API_TOKEN:
        raise RuntimeError(
            "Paperless API token not configured"
        )

    stats = api_json(
        f"{PAPERLESS_URL}/api/statistics/",
        headers={
            "Authorization":
                f"Token {PAPERLESS_API_TOKEN}",
        },
    )

    return {
        "available": True,
        "documents": int(
            stats.get("documents_total", 0) or 0
        ),
        "inbox": int(
            stats.get("documents_inbox", 0) or 0
        ),
        "correspondents": int(
            stats.get("correspondent_count", 0) or 0
        ),
        "document_types": int(
            stats.get("document_type_count", 0) or 0
        ),
        "tags": int(
            stats.get("tag_count", 0) or 0
        ),
    }



def subscribarr_metrics():
    if not SUBSCRIBARR_URL:
        return {
            "available": False,
            "error": "SUBSCRIBARR_URL not configured",
        }

    if not SUBSCRIBARR_API_KEY:
        return {
            "available": False,
            "error": "SUBSCRIBARR_API_KEY not configured",
        }

    payload = api_json(
        f"{SUBSCRIBARR_URL}/api/status/dashboard",
        headers={
            "X-Api-Key": SUBSCRIBARR_API_KEY,
        },
        timeout=8,
    )

    totals = payload.get("totals") or {}

    shows = payload.get("shows") or []
    if not isinstance(shows, list):
        shows = []

    active_updates = payload.get("active_updates") or []
    if not isinstance(active_updates, list):
        active_updates = []

    youtube_api = payload.get("youtube_api") or {}
    if not isinstance(youtube_api, dict):
        youtube_api = {}

    missing = sum(
        int(show.get("downloads_needed") or 0)
        for show in shows
        if isinstance(show, dict)
    )

    failed = int(
        totals.get("failed_downloads") or 0
    )

    unmatched = int(
        totals.get("unmatched_videos") or 0
    )

    updating = len(active_updates)

    youtube_enabled = (
        youtube_api.get("enabled") is True
    )

    youtube_configured = bool(
        youtube_api.get("configured")
    )

    youtube_available = bool(
        youtube_api.get("available")
    )

    youtube_paused = (
        youtube_enabled
        and youtube_configured
        and not youtube_available
    )

    if updating > 0:
        status_text = "Updating"
        status_level = "warning"

    elif failed > 0:
        status_text = "Attention"
        status_level = "critical"

    elif youtube_paused:
        status_text = "Degraded"
        status_level = "warning"

    else:
        status_text = "Healthy"
        status_level = "ok"

    return {
        "available": True,
        "healthy": status_level == "ok",
        "status_text": status_text,
        "status_level": status_level,

        "shows": int(
            totals.get("shows") or 0
        ),

        "episodes": int(
            totals.get("episodes") or 0
        ),

        "library": int(
            totals.get("library") or 0
        ),

        "missing": missing,
        "unmatched": unmatched,
        "failed": failed,
        "active_updates": updating,

        "youtube_enabled": youtube_enabled,
        "youtube_configured": youtube_configured,
        "youtube_available": youtube_available,
        "youtube_paused": youtube_paused,
        "youtube_disabled_until":
            youtube_api.get("disabled_until"),
    }


def storage_delta_text(value):
    if value is None:
        return ""

    value = int(value)

    if value > 0:
        sign = "+"
    else:
        sign = ""

    absolute = abs(value)

    if absolute >= 1_000_000_000_000:
        return (
            f"{sign}"
            f"{value / 1_000_000_000_000:.2f} TB"
        )

    if absolute >= 1_000_000_000:
        return (
            f"{sign}"
            f"{value / 1_000_000_000:.1f} GB"
        )

    if absolute >= 1_000_000:
        return (
            f"{sign}"
            f"{value / 1_000_000:.1f} MB"
        )

    if absolute >= 1_000:
        return (
            f"{sign}"
            f"{value / 1_000:.1f} KB"
        )

    return f"{sign}{value} B"


def storage_history_metrics():
    if not STORAGE_HISTORY_URL:
        return {
            "available": False,
            "error":
                "STORAGE_HISTORY_URL not configured",
        }

    payload = api_json(
        f"{STORAGE_HISTORY_URL}/summary",
        timeout=5,
    )

    series = payload.get("series")

    if not isinstance(series, list):
        raise RuntimeError(
            "Storage history returned invalid summary"
        )

    datasets = {}

    for item in series:
        if not isinstance(item, dict):
            continue

        dataset_id = str(
            item.get("id") or ""
        )

        if not dataset_id:
            continue

        change = item.get("change") or {}

        datasets[dataset_id] = {
            **item,
            "change_text": {
                period: storage_delta_text(
                    (
                        change.get(period)
                        or {}
                    ).get("change_bytes")
                )
                for period in (
                    "7d",
                    "30d",
                    "1y",
                )
            },
        }

    return {
        "available": True,
        "datasets": datasets,
    }


SERVICE_INTEGRATIONS = {
    # normalized stack: (service type, metrics cache key, refresh function)
    "qbittorrent": ("qbittorrent", "qbittorrent", qbit_metrics),
    "sonarr": ("sonarr", "sonarr", sonarr_metrics),
    "radarr": ("radarr", "radarr", radarr_metrics),
    "plex": ("plex", "plex", tautulli_metrics),
    "sportarr": ("sportarr", "sportarr", sportarr_metrics),
    "peanut": ("peanut", "peanut", peanut_metrics),
    "tailscale": ("tailscale", "tailscale", tailscale_metrics),
    "scrutiny": ("scrutiny", "scrutiny", scrutiny_metrics),
    "beszel": ("beszel", "beszel", beszel_metrics),
    "storagehistory": (
        "storage-history",
        "storage-history",
        storage_history_metrics,
    ),
    "immich": ("immich", "immich", immich_metrics),
    "jellyfin": ("jellyfin", "jellyfin", jellyfin_metrics),
    "prowlarr": ("prowlarr", "prowlarr", prowlarr_metrics),
    "bazarr": ("bazarr", "bazarr", bazarr_metrics),
    "uptimekuma": (
        "uptime-kuma",
        "uptime-kuma",
        uptime_kuma_metrics,
    ),
    "gatus": ("gatus", "gatus", gatus_metrics),
    "tdarr": ("tdarr", "tdarr", tdarr_metrics),
    "dispatcharr": (
        "dispatcharr",
        "dispatcharr",
        dispatcharr_metrics,
    ),
    "paperless": ("paperless", "paperless", paperless_metrics),
    "subscribarr": ("subscribarr", "subscribarr", subscribarr_metrics),
}

service_metrics_cache = {
    "updated": 0,
    "last_success": None,
    "last_error": None,
    **{
        cache_key: {}
        for _, cache_key, _ in SERVICE_INTEGRATIONS.values()
    },
}


def refresh_service_metrics():
    services = tuple(
        (cache_key, refresh_function)
        for _, cache_key, refresh_function
        in SERVICE_INTEGRATIONS.values()
    )

    def fetch_one(name, function):
        try:
            return name, function(), None
        except Exception as exc:
            return name, None, exc

    results = {}
    errors = []

    # These integrations are independent network calls. A small bounded
    # pool prevents one slow service from serially delaying every card.
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(8, len(services))
    ) as executor:
        futures = [
            executor.submit(fetch_one, name, function)
            for name, function in services
        ]

        for future in concurrent.futures.as_completed(futures):
            name, payload, exc = future.result()

            if exc is None:
                results[name] = payload
                continue

            error = f"{type(exc).__name__}: {exc}"
            errors.append(f"{name}: {error}")

            with service_metrics_lock:
                previous = copy.deepcopy(
                    service_metrics_cache.get(name, {})
                )

            if previous:
                previous["using_last_good"] = True
                previous["error"] = error
                results[name] = previous
            else:
                results[name] = {
                    "available": False,
                    "error": error,
                    "using_last_good": False,
                }

    now = time.time()

    with service_metrics_lock:
        for name, payload in results.items():
            payload = dict(payload)
            payload.setdefault("using_last_good", False)
            service_metrics_cache[name] = payload

        service_metrics_cache["updated"] = now
        service_metrics_cache["last_error"] = (
            "; ".join(sorted(errors)) if errors else None
        )

        if not errors:
            service_metrics_cache["last_success"] = now


def ensure_service_metrics_fresh():
    """
    Refresh service metrics only when something actually requests them.

    SERVICE_METRICS_TTL is now a cache freshness threshold rather than
    a permanent polling interval.

    The refresh lock prevents simultaneous browser requests from
    causing duplicate service sweeps.
    """
    now = time.time()

    with service_metrics_lock:
        updated = (
            service_metrics_cache.get("updated")
            or 0
        )

    if (
        updated
        and now - updated < SERVICE_METRICS_TTL
    ):
        return

    with service_metrics_refresh_lock:
        # Another request may have completed the refresh while this
        # request was waiting for the lock.
        now = time.time()

        with service_metrics_lock:
            updated = (
                service_metrics_cache.get("updated")
                or 0
            )

        if (
            updated
            and now - updated < SERVICE_METRICS_TTL
        ):
            return

        started = time.monotonic()

        try:
            refresh_service_metrics()

            elapsed = (
                time.monotonic()
                - started
            )

            print(
                "Service metrics refresh OK "
                f"({elapsed:.2f}s)",
                flush=True,
            )

        except Exception as exc:
            print(
                "service metrics refresh failed: "
                f"{exc}",
                flush=True,
            )


def service_metrics_snapshot():
    ensure_service_metrics_fresh()

    with service_metrics_lock:
        return copy.deepcopy(
            service_metrics_cache
        )



# =============================================================================
# DOCKER SOCKET
# =============================================================================

def docker_request(path):
    return unix_socket_json_request(
        DOCKER_SOCKET,
        path,
        host="docker",
        timeout=5,
        label="Docker API",
    )


# =============================================================================
# SHARED OVERRIDES
# =============================================================================

def load_overrides():
    try:
        mtime = os.path.getmtime(
            OVERRIDES_FILE
        )

    except OSError as exc:
        with overrides_lock:
            overrides_cache["error"] = str(exc)

        return overrides_cache

    with overrides_lock:
        if (
            overrides_cache["mtime"]
            == mtime
        ):
            return overrides_cache

        try:
            with open(
                OVERRIDES_FILE,
                "r",
            ) as f:
                data = yaml.safe_load(f) or {}

            groups = data.get(
                "groups",
                {},
            )

            names = data.get(
                "names",
                {},
            )

            icons = data.get(
                "icons",
                {},
            )

            portals = data.get(
                "portals",
                {},
            )

            order = data.get(
                "order",
                {},
            )

            if not isinstance(groups, dict):
                groups = {}

            if not isinstance(names, dict):
                names = {}

            if not isinstance(icons, dict):
                icons = {}

            if not isinstance(portals, dict):
                portals = {}

            if not isinstance(order, dict):
                order = {}

            overrides_cache["mtime"] = mtime
            overrides_cache["groups"] = groups
            overrides_cache["names"] = names
            overrides_cache["icons"] = icons
            overrides_cache["portals"] = portals
            overrides_cache["order"] = order
            overrides_cache["error"] = None

            print(
                "overrides reloaded: "
                f"{len(groups)} groups, "
                f"{len(names)} names, "
                f"{len(icons)} icons, "
                f"{len(portals)} portals",
                flush=True,
            )

        except Exception as exc:
            overrides_cache["error"] = str(exc)

            print(
                "override reload failed: "
                f"{exc}",
                flush=True,
            )

        return overrides_cache


# =============================================================================
# HTTP HELPERS
# =============================================================================

def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent":
                "glance-docker-data/7.0",
        },
    )

    with urllib.request.urlopen(
        req,
        timeout=20,
    ) as response:
        return json.load(response)


# =============================================================================
# NORMALIZATION
# =============================================================================

def normalize(value):
    if not value:
        return ""

    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(value)
        .lower()
        .strip(),
    )


def icon_reference(value):
    if not value:
        return ""

    value = (
        str(value)
        .lower()
        .strip()
    )

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    return value.strip("-")


def friendly_name(value):
    value = (
        str(value)
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )

    return " ".join(
        word.capitalize()
        for word in value.split()
    )


# =============================================================================
# SELFH.ST CATALOG
# =============================================================================

def rebuild_catalog():
    projects = fetch_json(
        SELFHST_PROJECTS_URL
    )

    index = {}

    for project in projects:
        keys = set()

        for value in (
            project.get("Project"),
            project.get("Reference"),
            project.get("Repository"),
        ):
            key = normalize(
                value
            )

            if key:
                keys.add(
                    key
                )

        repository = (
            project.get("Repository")
            or ""
        )

        if repository:
            parts = repository.split(
                "/"
            )

            if parts:
                keys.add(
                    normalize(
                        parts[-1]
                    )
                )

        for key in keys:
            index.setdefault(
                key,
                project,
            )

    catalog_cache["projects"] = projects
    catalog_cache["index"] = index
    catalog_cache["updated"] = time.time()
    catalog_cache["error"] = None

    print(
        "selfh.st catalog loaded: "
        f"{len(projects)} projects / "
        f"{len(index)} aliases",
        flush=True,
    )


def ensure_catalog():
    with catalog_lock:
        stale = (
            not catalog_cache["index"]
            or time.time()
            - catalog_cache["updated"]
            >= CATALOG_TTL
        )

        if not stale:
            return

        try:
            rebuild_catalog()

        except Exception as exc:
            catalog_cache["error"] = str(exc)

            print(
                "selfh.st catalog refresh failed: "
                f"{exc}",
                flush=True,
            )


def match_catalog(
    stack_name,
    members,
):
    ensure_catalog()

    index = catalog_cache[
        "index"
    ]

    candidates = [
        stack_name,
    ]

    for member in members:
        candidates.append(
            member.get(
                "name",
                "",
            )
        )

        labels = (
            member.get("labels")
            or {}
        )

        service = labels.get(
            "com.docker.compose.service"
        )

        if service:
            candidates.append(
                service
            )

    seen = set()

    for candidate in candidates:
        key = normalize(
            candidate
        )

        if (
            not key
            or key in seen
        ):
            continue

        seen.add(
            key
        )

        if key in index:
            return index[
                key
            ]

        for suffix in (
            "server",
            "app",
            "web",
            "service",
            "container",
        ):
            if key.endswith(
                suffix
            ):
                trimmed = key[
                    :-len(suffix)
                ]

                if trimmed in index:
                    return index[
                        trimmed
                    ]

    return None


# =============================================================================
# HOMEPAGE LABELS
# =============================================================================

def homepage_metadata(members):
    for member in members:
        labels = (
            member.get("labels")
            or {}
        )

        name = labels.get(
            "homepage.name"
        )

        group = labels.get(
            "homepage.group"
        )

        icon = labels.get(
            "homepage.icon"
        )

        if name or group or icon:
            return {
                "name": name,
                "group": group,
                "icon": icon,
            }

    return {}


def normalize_group(group):
    if not group:
        return None

    lowered = (
        str(group)
        .strip()
        .lower()
    )

    aliases = {
        "media":
            "Media",

        "photos":
            "Media",

        "photo":
            "Media",

        "downloads":
            "Downloads",

        "download":
            "Downloads",

        "arr":
            "Downloads",

        "*arr":
            "Downloads",

        "monitoring":
            "Monitoring",

        "observability":
            "Monitoring",

        "infrastructure":
            "Infrastructure",

        "infra":
            "Infrastructure",

        "system":
            "Infrastructure",

        "tools":
            "Tools",

        "utilities":
            "Tools",

        "other":
            "Other",
    }

    return aliases.get(
        lowered,
        group,
    )


def is_generic_docker_icon(url):
    if not url:
        return False

    lower = str(
        url
    ).lower()

    return (
        lower.endswith(
            "/docker.png"
        )
        or "/docker.png?"
        in lower
        or lower.endswith(
            "/docker.webp"
        )
        or lower.endswith(
            "/docker.svg"
        )
    )


# =============================================================================
# CATEGORY
# =============================================================================

def category_from_tags(tags):
    tag_set = {
        tag.strip().lower()
        for tag in tags
        if tag.strip()
    }

    if tag_set & DOWNLOAD_TAGS:
        return "Downloads"

    if tag_set & MEDIA_TAGS:
        return "Media"

    if tag_set & MONITORING_TAGS:
        return "Monitoring"

    if tag_set & INFRA_TAGS:
        return "Infrastructure"

    if tag_set:
        return "Tools"

    return "Other"


# =============================================================================
# ICON RESOLUTION
# =============================================================================

def candidate_icon_references(
    stack_name,
    display_name,
    catalog,
):
    overrides = load_overrides()

    candidates = []

    override = (
        overrides["icons"]
        .get(
            stack_name
        )
    )

    if override:
        candidates.append(
            override
        )

    candidates.append(
        icon_reference(
            display_name
        )
    )

    candidates.append(
        icon_reference(
            stack_name
        )
    )

    if catalog:
        reference = catalog.get(
            "Reference"
        )

        project = catalog.get(
            "Project"
        )

        if reference:
            candidates.append(
                icon_reference(
                    reference
                )
            )

        if project:
            candidates.append(
                icon_reference(
                    project
                )
            )

    result = []
    seen = set()

    for value in candidates:
        if (
            value
            and value not in seen
        ):
            seen.add(
                value
            )

            result.append(
                value
            )

    return result


def resolve_icon(
    stack_name,
    display_name,
    homepage,
    catalog,
):
    overrides = load_overrides()

    references = (
        candidate_icon_references(
            stack_name,
            display_name,
            catalog,
        )
    )

    override = (
        overrides["icons"]
        .get(
            stack_name
        )
    )

    # Explicit icon override first.
    if override:
        return (
            f"{DASHBOARD_ICON_BASE}/{override}.png",
            "override-dashboard-icons",
        )

    # Existing Homepage icon if it isn't the old Docker fallback.
    homepage_icon = (
        homepage.get(
            "icon"
        )
    )

    if (
        homepage_icon
        and not is_generic_docker_icon(
            homepage_icon
        )
    ):
        return (
            homepage_icon,
            "homepage",
        )

    # If catalog has a known reference, prefer Dashboard Icons naming.
    if references:
        reference = references[0]

        return (
            f"{DASHBOARD_ICON_BASE}/{reference}.png",
            "dashboard-icons",
        )

    # Last usable catalog icon.
    if catalog:
        catalog_icon = (
            catalog.get(
                "Icon"
            )
        )

        if catalog_icon:
            return (
                catalog_icon,
                "selfhst-catalog",
            )

    return (
        "",
        "none",
    )


# =============================================================================
# PORTAL INFERENCE
# =============================================================================

def infer_portal(
    stack_name,
    members,
    overrides,
):
    portal = (
        overrides["portals"]
        .get(
            stack_name,
            {},
        )
    )

    if not isinstance(
        portal,
        dict,
    ):
        portal = {}

    # -------------------------------------------------------------------------
    # Explicitly disable portal detection for this stack.
    #
    # Useful for containers such as Media Tools where the only published
    # TCP port is SSH rather than a web interface.
    # -------------------------------------------------------------------------

    if portal.get(
        "disabled",
        False,
    ):
        return {
            "port":
                0,

            "path":
                "/",

            "scheme":
                "",

            "source":
                "disabled",
        }

    # -------------------------------------------------------------------------
    # Explicit port override
    # -------------------------------------------------------------------------

    try:
        explicit_port = int(
            portal.get(
                "port",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        explicit_port = 0

    port = explicit_port

    # -------------------------------------------------------------------------
    # Automatic published-port detection
    # -------------------------------------------------------------------------

    if port == 0:
        preferred = [
            member
            for member in members
            if (
                member.get(
                    "labels",
                    {},
                ).get(
                    "homepage.name"
                )
                or member.get(
                    "labels",
                    {},
                ).get(
                    "homepage.group"
                )
            )
        ]

        candidates = (
            preferred
            if preferred
            else members
        )

        ports = []

        for member in candidates:
            for published_port in member.get(
                "published_ports",
                [],
            ):
                if (
                    published_port
                    not in ports
                ):
                    ports.append(
                        published_port
                    )

        if len(
            ports
        ) == 1:
            port = ports[
                0
            ]

    # -------------------------------------------------------------------------
    # Path
    # -------------------------------------------------------------------------

    path = str(
        portal.get(
            "path",
            "/",
        )
        or "/"
    )

    if not path.startswith(
        "/"
    ):
        path = (
            "/"
            + path
        )

    # -------------------------------------------------------------------------
    # Scheme
    #
    # Blank = retain whatever scheme was used to open Glance.
    # -------------------------------------------------------------------------

    scheme = str(
        portal.get(
            "scheme",
            "",
        )
        or ""
    ).lower()

    if scheme not in (
        "",
        "http",
        "https",
    ):
        scheme = ""

    return {
        "port":
            port,

        "path":
            path,

        "scheme":
            scheme,

        "source":
            (
                "override"
                if explicit_port
                else (
                    "published-port"
                    if port
                    else "none"
                )
            ),
    }

# =============================================================================
# APPLICATION METADATA
# =============================================================================

def app_metadata(
    stack_name,
    members,
):
    overrides = load_overrides()

    homepage = homepage_metadata(
        members
    )

    catalog = match_catalog(
        stack_name,
        members,
    )

    # -------------------------------------------------------------------------
    # NAME
    # -------------------------------------------------------------------------

    if stack_name in overrides["names"]:
        display_name = (
            overrides["names"][
                stack_name
            ]
        )

        name_source = "override"

    elif homepage.get(
        "name"
    ):
        display_name = homepage[
            "name"
        ]

        name_source = "homepage"

    elif (
        catalog
        and catalog.get(
            "Project"
        )
    ):
        display_name = catalog[
            "Project"
        ]

        name_source = "selfhst"

    else:
        display_name = friendly_name(
            stack_name
        )

        name_source = "inferred"

    # -------------------------------------------------------------------------
    # GROUP
    # -------------------------------------------------------------------------

    if stack_name in overrides["groups"]:
        group = (
            overrides["groups"][
                stack_name
            ]
        )

        group_source = "override"

    elif homepage.get(
        "group"
    ):
        group = normalize_group(
            homepage[
                "group"
            ]
        )

        group_source = "homepage"

    elif catalog:
        raw_tags = (
            catalog.get(
                "Tags"
            )
            or ""
        )

        tags = [
            tag.strip()
            for tag
            in raw_tags.split(
                ","
            )
            if tag.strip()
        ]

        group = category_from_tags(
            tags
        )

        group_source = "selfhst"

    else:
        group = "Other"
        group_source = "fallback"

    # -------------------------------------------------------------------------
    # ICON
    # -------------------------------------------------------------------------

    icon, icon_source = (
        resolve_icon(
            stack_name,
            display_name,
            homepage,
            catalog,
        )
    )

    # -------------------------------------------------------------------------
    # PORTAL
    # -------------------------------------------------------------------------

    portal = infer_portal(
        stack_name,
        members,
        overrides,
    )

    return {
        "display_name":
            display_name,

        "group":
            group,

        "icon":
            icon,

        "portal_port":
            portal[
                "port"
            ],

        "portal_path":
            portal[
                "path"
            ],

        "portal_scheme":
            portal[
                "scheme"
            ],

        "portal_source":
            portal[
                "source"
            ],

        "name_source":
            name_source,

        "group_source":
            group_source,

        "icon_source":
            icon_source,

        "reference":
            (
                catalog.get(
                    "Reference"
                )
                if catalog
                else None
            ),

        "tags":
            (
                catalog.get(
                    "Tags",
                    ""
                )
                if catalog
                else ""
            ),
    }


# =============================================================================
# DOCKHAND UPDATE STATUS
# =============================================================================

DOCKHAND_MANAGER_PROJECTS = {
    "dockhand",
    "ix-dockhand",
}


def is_dockhand_manager_name(value):
    return (
        str(value or "")
        .strip()
        .lower()
        in DOCKHAND_MANAGER_PROJECTS
    )


def dockhand_pending_updates():
    if not DOCKHAND_URL:
        return []

    url = (
        f"{DOCKHAND_URL}"
        "/api/containers/pending-updates"
        f"?env={DOCKHAND_ENV_ID}"
    )

    payload = fetch_json(
        url
    )

    if not isinstance(
        payload,
        dict,
    ):
        return []

    pending = payload.get(
        "pendingUpdates",
        [],
    )

    return (
        pending
        if isinstance(
            pending,
            list,
        )
        else []
    )


def normalize_update_matches(items):
    matches = set()

    for item in items:
        if isinstance(
            item,
            str,
        ):
            matches.add(
                item.lstrip(
                    "/"
                )
            )

            continue

        if not isinstance(
            item,
            dict,
        ):
            continue

        for key in (
            "id",
            "containerId",
            "container_id",
            "containerID",
        ):
            value = item.get(
                key
            )

            if value:
                matches.add(
                    str(
                        value
                    )
                )

        for key in (
            "name",
            "containerName",
            "container_name",
        ):
            value = item.get(
                key
            )

            if value:
                matches.add(
                    str(
                        value
                    ).lstrip(
                        "/"
                    )
                )

    return matches


def container_update_available(
    container_id,
    name,
    matches,
):
    if (
        name in matches
        or container_id in matches
    ):
        return True

    for value in matches:
        if (
            len(value) >= 8
            and container_id.startswith(
                value
            )
        ):
            return True

    return False


# =============================================================================
# CONTAINER HEALTH + PORTS
# =============================================================================

def classify_container(
    summary,
):
    state = (
        summary.get(
            "State",
            "",
        )
        or ""
    ).lower()

    running = (
        state == "running"
    )

    status = (
        summary.get(
            "Status",
            "",
        )
        or ""
    ).lower()

    # Docker includes health state directly in the container-list
    # Status field:
    #
    #   Up 5 minutes (healthy)
    #   Up 5 minutes (unhealthy)
    #   Up 5 seconds (health: starting)
    #
    # Containers without a healthcheck have no health suffix.
    if "(healthy)" in status:
        has_healthcheck = True
        health_status = "healthy"

    elif "(unhealthy)" in status:
        has_healthcheck = True
        health_status = "unhealthy"

    elif "(health: starting)" in status:
        has_healthcheck = True
        health_status = "starting"

    else:
        has_healthcheck = False
        health_status = None

    if not running:
        color = "red"

    elif not has_healthcheck:
        color = "green"

    elif health_status == "healthy":
        color = "green"

    else:
        color = "yellow"

    names = summary.get(
        "Names",
        [],
    )

    name = (
        names[
            0
        ].lstrip(
            "/"
        )
        if names
        else summary.get(
            "Id",
            "",
        )[:12]
    )

    # -------------------------------------------------------------------------
    # Published TCP ports
    # -------------------------------------------------------------------------

    published_ports = []

    for port in summary.get(
        "Ports",
        [],
    ):
        if (
            port.get(
                "Type"
            )
            != "tcp"
        ):
            continue

        public_port = port.get(
            "PublicPort"
        )

        if not public_port:
            continue

        try:
            public_port = int(
                public_port
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        if (
            public_port
            not in published_ports
        ):
            published_ports.append(
                public_port
            )

    published_ports.sort()

    return {
        "id":
            summary.get(
                "Id",
                "",
            ),

        "name":
            name,

        "image":
            summary.get(
                "Image",
                "",
            ),

        "labels":
            summary.get(
                "Labels",
                {},
            ) or {},

        "running":
            running,

        "has_healthcheck":
            has_healthcheck,

        "health_status":
            health_status,

        "color":
            color,

        "published_ports":
            published_ports,
    }


# =============================================================================
# STACK AGGREGATION
# =============================================================================

def build_stack(
    name,
    members,
    metrics,
):
    total = len(
        members
    )

    running = sum(
        1
        for member in members
        if member[
            "running"
        ]
    )

    yellow = sum(
        1
        for member in members
        if member[
            "color"
        ] == "yellow"
    )

    red = sum(
        1
        for member in members
        if member[
            "color"
        ] == "red"
    )

    if running == 0:
        color = "red"

    elif (
        running < total
        or yellow > 0
        or red > 0
    ):
        color = "yellow"

    else:
        color = "green"

    updates = sum(
        1
        for member in members
        if member[
            "update_available"
        ]
    )

    meta = app_metadata(
        name,
        members,
    )

    service = {}

    normalized_stack = normalize(name)
    integration = SERVICE_INTEGRATIONS.get(normalized_stack)

    if integration:
        service_type, cache_key, _ = integration
        service = {
            "type": service_type,
            **metrics.get(cache_key, {}),
        }

    return {
        "name":
            name,

        "display_name":
            meta[
                "display_name"
            ],

        "group":
            meta[
                "group"
            ],

        "icon":
            meta[
                "icon"
            ],

        "portal_port":
            meta[
                "portal_port"
            ],

        "portal_path":
            meta[
                "portal_path"
            ],

        "portal_scheme":
            meta[
                "portal_scheme"
            ],

        "portal_source":
            meta[
                "portal_source"
            ],

        "name_source":
            meta[
                "name_source"
            ],

        "group_source":
            meta[
                "group_source"
            ],

        "icon_source":
            meta[
                "icon_source"
            ],

        "containers":
            total,

        "running":
            running,

        "color":
            color,

        "updates":
            updates,

        "update_available":
            updates > 0,

        "service":
            service,

        "members":
            sorted(
                members,
                key=lambda x:
                    x[
                        "name"
                    ].lower(),
            ),
    }


def docker_stack_data():
    summaries = docker_request(
        "/containers/json?all=true"
    )

    # -------------------------------------------------------------------------
    # Dockhand updates
    # -------------------------------------------------------------------------

    try:
        pending = (
            dockhand_pending_updates()
        )

        update_matches = (
            normalize_update_matches(
                pending
            )
        )

        update_source_ok = True
        update_error = None

    except Exception as exc:
        update_matches = set()
        update_source_ok = False
        update_error = str(
            exc
        )

    # -------------------------------------------------------------------------
    # Build project/container map
    # -------------------------------------------------------------------------

    projects = {}
    standalone = []

    for summary in summaries:
        labels = (
            summary.get(
                "Labels"
            )
            or {}
        )

        project = labels.get(
            "com.docker.compose.project"
        )

        member = classify_container(
            summary,
        )

        member[
            "update_available"
        ] = container_update_available(
            member[
                "id"
            ],
            member[
                "name"
            ],
            update_matches,
        )

        if project:
            projects.setdefault(
                project,
                [],
            ).append(
                member
            )

        else:
            standalone.append(
                member
            )

    # -------------------------------------------------------------------------
    # Aggregate stacks
    # -------------------------------------------------------------------------

    stacks = []

    # Take one immutable service snapshot for the entire response. This
    # avoids repeatedly locking/copying the same cache for every stack and
    # guarantees all cards in this response use the same metric generation.
    metrics = service_metrics_snapshot()

    for project, members in (
        projects.items()
    ):
        stacks.append(
            build_stack(
                project,
                members,
                metrics,
            )
        )

    for member in standalone:
        stacks.append(
            build_stack(
                member[
                    "name"
                ],
                [
                    member
                ],
                metrics,
            )
        )

    # -------------------------------------------------------------------------
    # Global update summary for Dockhand
    # -------------------------------------------------------------------------

    stacks_with_updates = sum(
        1
        for stack in stacks
        if (
            not is_dockhand_manager_name(
                stack.get("name", "")
            )
            and stack.get(
                "update_available"
            )
        )
    )

    for stack in stacks:
        if is_dockhand_manager_name(stack.get("name", "")):
            # Dockhand is the update manager, not one of its managed apps.
            # TrueNAS owns updates for this container.
            stack["updates"] = 0
            stack["update_available"] = False

            stack["service"] = {
                "type": "dockhand",
                "available": True,
                "updates_available":
                    stacks_with_updates,
                "healthy":
                    stacks_with_updates == 0,
            }
            break

    # -------------------------------------------------------------------------
    # Sort
    # -------------------------------------------------------------------------

    group_index = {
        group: index
        for index, group
        in enumerate(
            GROUP_ORDER
        )
    }

    configured_order = (
        load_overrides().get(
            "order",
            {},
        )
        or {}
    )

    order_by_group = {}

    for group_name, stack_names in (
        configured_order.items()
    ):
        if not isinstance(
            stack_names,
            list,
        ):
            continue

        group_key = normalize(
            group_name
        )

        ranks = {}

        for rank, stack_name in enumerate(
            stack_names
        ):
            stack_key = normalize(
                stack_name
            )

            if (
                stack_key
                and stack_key not in ranks
            ):
                ranks[stack_key] = rank

        order_by_group[group_key] = ranks

    def stack_sort_key(item):
        ranks = order_by_group.get(
            normalize(
                item.get(
                    "group",
                    "",
                )
            ),
            {},
        )

        stack_key = normalize(
            item.get(
                "name",
                "",
            )
        )

        if stack_key in ranks:
            return (
                group_index.get(
                    item["group"],
                    999,
                ),
                0,
                ranks[stack_key],
                "",
            )

        return (
            group_index.get(
                item["group"],
                999,
            ),
            1,
            0,
            item[
                "display_name"
            ].lower(),
        )

    stacks.sort(
        key=stack_sort_key
    )

    # -------------------------------------------------------------------------
    # Groups
    # -------------------------------------------------------------------------

    group_names = []

    for preferred in GROUP_ORDER:
        if any(
            stack[
                "group"
            ] == preferred
            for stack in stacks
        ):
            group_names.append(
                preferred
            )

    for stack in stacks:
        group = stack[
            "group"
        ]

        if (
            group
            not in group_names
        ):
            group_names.append(
                group
            )

    groups = []

    for group in group_names:
        apps = [
            stack
            for stack in stacks
            if stack[
                "group"
            ] == group
        ]

        if apps:
            groups.append({
                "name":
                    group,

                "stacks":
                    apps,
            })

    return {
        "total_stacks":
            len(
                stacks
            ),

        "total_containers":
            len(
                summaries
            ),

        "updates_available":
            sum(
                stack[
                    "updates"
                ]
                for stack in stacks
            ),

        "update_source_ok":
            update_source_ok,

        "update_error":
            update_error,

        "overrides_error":
            load_overrides()[
                "error"
            ],

        "groups":
            groups,

        "stacks":
            stacks,
    }


# =============================================================================
# HTTP SERVER
# =============================================================================

# =============================================================================
# HOME ASSISTANT LIVE METRICS
# =============================================================================

home_metrics_lock = threading.Lock()
home_metrics_refresh_lock = threading.Lock()

home_metrics_cache = {
    "timestamp": 0,
    "data": None,
}



def home_metrics():
    now_ts = time.time()

    with home_metrics_lock:
        cached = home_metrics_cache["data"]
        timestamp = home_metrics_cache["timestamp"]

    if (
        cached is not None
        and now_ts - timestamp < HOME_METRICS_TTL
    ):
        return copy.deepcopy(cached)

    with home_metrics_refresh_lock:
        # A second request may have refreshed while we waited.
        now_ts = time.time()

        with home_metrics_lock:
            cached = home_metrics_cache["data"]
            timestamp = home_metrics_cache["timestamp"]

        if (
            cached is not None
            and now_ts - timestamp < HOME_METRICS_TTL
        ):
            return copy.deepcopy(cached)

        mercedes_entities = {
            "charging_status": "sensor.4jgfb4gb2sb320653_charging_status",
            "charging_power": "sensor.4jgfb4gb2sb320653_charging_power",
            "battery": "sensor.4jgfb4gb2sb320653_state_of_charge",
            "charge_limit": "sensor.4jgfb4gb2sb320653_max_state_of_charge",
            "electric_range": "sensor.4jgfb4gb2sb320653_range_electric",
            "fuel": "sensor.4jgfb4gb2sb320653_fuel_level",
            "gas_range": "sensor.4jgfb4gb2sb320653_range_liquid",
            "charge_complete": "sensor.4jgfb4gb2sb320653_end_of_charge",
            "charge_program": "sensor.4jgfb4gb2sb320653_selected_charge_program",
            "lock": "lock.4jgfb4gb2sb320653_lock",
            "climate": "switch.4jgfb4gb2sb320653_pre_entry_climate_control",
        }

        humidor_entities = {
            "top_shelf": {
                "temperature": "sensor.h5074_9673_temperature",
                "humidity": "sensor.h5074_9673_humidity",
            },
            "middle_back": {
                "temperature": "sensor.h5074_db0e_temperature",
                "humidity": "sensor.h5074_db0e_humidity",
            },
            "middle_front": {
                "temperature": "sensor.h5074_ba14_temperature",
                "humidity": "sensor.h5074_ba14_humidity",
            },
            "drawer": {
                "temperature": "sensor.wineador_drawer_temperature",
                "humidity": "sensor.wineador_drawer_humidity",
            },
            "bottom_shelf": {
                "temperature": "sensor.h5074_927b_temperature",
                "humidity": "sensor.h5074_927b_humidity",
            },
            "humidor": {
                "temperature": "sensor.h5074_059f_temperature",
                "humidity": "sensor.h5074_059f_humidity",
            },
        }

        try:
            if not HA_URL or not HA_TOKEN:
                raise RuntimeError("Home Assistant is not configured")

            # One HA snapshot replaces 23 independent entity requests.
            all_states = api_json(
                f"{HA_URL}/api/states",
                headers={
                    "Authorization": f"Bearer {HA_TOKEN}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )

            state_index = {
                item.get("entity_id"): item
                for item in all_states
                if isinstance(item, dict) and item.get("entity_id")
            }

            def state_value(entity_id):
                item = state_index.get(entity_id) or {}
                attrs = item.get("attributes") or {}
                return {
                    "state": item.get("state"),
                    "unit": attrs.get("unit_of_measurement"),
                }

            mercedes = {
                key: state_value(entity_id)
                for key, entity_id in mercedes_entities.items()
            }

            humidor = {
                name: {
                    "temperature": state_value(entities["temperature"]),
                    "humidity": state_value(entities["humidity"]),
                }
                for name, entities in humidor_entities.items()
            }

            result = {
                "mercedes": mercedes,
                "humidor": humidor,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "stale": False,
            }

            with home_metrics_lock:
                home_metrics_cache["timestamp"] = time.time()
                home_metrics_cache["data"] = copy.deepcopy(result)

            return result

        except Exception as exc:
            # Preserve the last known good dashboard instead of blanking the
            # widget during a transient HA outage.
            with home_metrics_lock:
                cached = copy.deepcopy(home_metrics_cache["data"])

            if cached is not None:
                cached["stale"] = True
                cached["error"] = str(exc)
                return cached

            raise



# =============================================================================
# TRUENAS / NETDATA METRICS
# =============================================================================

def netdata_allmetrics():
    if not NETDATA_URL:
        raise RuntimeError(
            "NETDATA_URL is not configured"
        )

    return api_json(
        f"{NETDATA_URL}/api/v3/allmetrics?format=json",
        timeout=5,
    )


def netdata_dimension(
    metrics,
    chart,
    dimension,
):
    try:
        raw = (
            metrics[chart]
            ["dimensions"]
            [dimension]
            ["value"]
        )

        value = float(raw)

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            "missing Netdata metric: "
            f"{chart}/{dimension}"
        ) from exc

    return value


def build_truenas_metrics(metrics):
    idle = netdata_dimension(
        metrics,
        "system.cpu",
        "idle",
    )

    cpu_usage = max(
        0.0,
        min(
            100.0,
            100.0 - idle,
        ),
    )

    ram_free = netdata_dimension(
        metrics,
        "system.ram",
        "free",
    )

    ram_used = netdata_dimension(
        metrics,
        "system.ram",
        "used",
    )

    ram_cached = netdata_dimension(
        metrics,
        "system.ram",
        "cached",
    )

    ram_buffers = netdata_dimension(
        metrics,
        "system.ram",
        "buffers",
    )

    ram_total = (
        ram_free
        + ram_used
        + ram_cached
        + ram_buffers
    )

    ram_usage = (
        ram_used
        / ram_total
        * 100.0
        if ram_total > 0
        else 0.0
    )

    def pool(name):
        return {
            "utilization":
                netdata_dimension(
                    metrics,
                    (
                        f"zfspool.zfspool_{name}"
                        "_space_utilization"
                    ),
                    "utilization",
                ),

            "used":
                netdata_dimension(
                    metrics,
                    (
                        f"zfspool.zfspool_{name}"
                        "_space_usage"
                    ),
                    "used",
                ),

            "online":
                (
                    netdata_dimension(
                        metrics,
                        (
                            f"zfspool.zfspool_{name}"
                            "_health_state"
                        ),
                        "online",
                    )
                    == 1.0
                ),
        }

    def drive(
        device,
        device_type,
    ):
        prefix = (
            f"smartctl.device_{device}"
            f"_type_{device_type}"
        )

        return {
            "healthy":
                (
                    netdata_dimension(
                        metrics,
                        f"{prefix}_smart_status",
                        "passed",
                    )
                    == 1.0
                ),

            "temperature":
                netdata_dimension(
                    metrics,
                    f"{prefix}_temperature",
                    "temperature",
                ),
        }

    return {
        "cpu": {
            "usage":
                cpu_usage,
        },

        "ram": {
            "usage":
                ram_usage,

            "free_mib":
                ram_free,

            "used_mib":
                ram_used,

            "cached_mib":
                ram_cached,

            "buffers_mib":
                ram_buffers,

            "total_mib":
                ram_total,
        },

        "pools": {
            "NVME_4TB":
                pool(
                    "NVME_4TB"
                ),

            "NVME_TMP":
                pool(
                    "NVME_TMP"
                ),

            "SATA_16TB":
                pool(
                    "SATA_16TB"
                ),
        },

        "drives": {
            "nvme0":
                drive(
                    "nvme0",
                    "nvme",
                ),

            "nvme1":
                drive(
                    "nvme1",
                    "nvme",
                ),

            "nvme2":
                drive(
                    "nvme2",
                    "nvme",
                ),

            "sda":
                drive(
                    "sda",
                    "sat",
                ),

            "sdb":
                drive(
                    "sdb",
                    "sat",
                ),

            "sdc":
                drive(
                    "sdc",
                    "sat",
                ),

            "sdd":
                drive(
                    "sdd",
                    "sat",
                ),

            "sde":
                drive(
                    "sde",
                    "sat",
                ),

            "sdf":
                drive(
                    "sdf",
                    "sat",
                ),
        },
    }


def truenas_metrics():
    now = time.time()

    with truenas_metrics_lock:
        cached = truenas_metrics_cache[
            "data"
        ]

        age = (
            now
            - truenas_metrics_cache[
                "updated"
            ]
        )

        if (
            cached is not None
            and age < TRUENAS_METRICS_TTL
        ):
            return cached


    with truenas_metrics_refresh_lock:
        now = time.time()

        # Another request may have refreshed the cache
        # while this request waited for the refresh lock.
        with truenas_metrics_lock:
            cached = truenas_metrics_cache[
                "data"
            ]

            age = (
                now
                - truenas_metrics_cache[
                    "updated"
                ]
            )

            if (
                cached is not None
                and age < TRUENAS_METRICS_TTL
            ):
                return cached

        try:
            raw = netdata_allmetrics()

            data = build_truenas_metrics(
                raw
            )

            refreshed = time.time()

            data["updated"] = refreshed
            data["stale"] = False

            with truenas_metrics_lock:
                truenas_metrics_cache[
                    "updated"
                ] = refreshed

                truenas_metrics_cache[
                    "data"
                ] = data

                truenas_metrics_cache[
                    "last_error"
                ] = None

            print(
                "TrueNAS metrics refresh OK",
                flush=True,
            )

            return data

        except Exception as exc:
            with truenas_metrics_lock:
                truenas_metrics_cache[
                    "last_error"
                ] = str(exc)

                cached = truenas_metrics_cache[
                    "data"
                ]

            if cached is not None:
                stale = dict(cached)

                stale["stale"] = True
                stale["error"] = str(exc)

                return stale

            raise


class Handler(
    BaseHTTPRequestHandler
):
    def send_json(
        self,
        payload,
        status=200,
    ):
        body = json.dumps(
            payload
        ).encode()

        self.send_response(
            status
        )

        self.send_header(
            "Content-Type",
            "application/json",
        )

        self.send_header(
            "Cache-Control",
            "no-store",
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*",
        )

        self.send_header(
            "Content-Length",
            str(
                len(
                    body
                )
            ),
        )

        self.end_headers()

        self.wfile.write(
            body
        )

    def origin_allowed(
        self,
        origin,
    ):
        if not origin:
            # Non-browser callers such as localhost curl.
            return True

        try:
            parsed_origin = (
                urllib.parse.urlparse(
                    origin
                )
            )

            host_header = (
                self.headers.get(
                    "Host",
                    ""
                )
            )

            helper_host = (
                urllib.parse.urlsplit(
                    f"//{host_header}"
                ).hostname
                or ""
            ).lower()

            origin_host = (
                parsed_origin.hostname
                or ""
            ).lower()

            origin_port = (
                parsed_origin.port
            )

            if origin_port is None:
                origin_port = (
                    443
                    if parsed_origin.scheme
                    == "https"
                    else 80
                )

            return (
                parsed_origin.scheme
                in ("http", "https")
                and origin_host
                == helper_host
                and origin_port
                in (30080, 30081)
            )

        except Exception:
            return False

    def post_allowed(self, origin):
        if origin:
            return self.origin_allowed(origin)

        # Originless management requests are useful for local diagnostics,
        # but should not expose redeploy/update actions to the entire LAN.
        client_host = str(self.client_address[0]).split("%", 1)[0]
        return client_host in {"127.0.0.1", "::1"}

    def do_OPTIONS(self):
        origin = self.headers.get(
            "Origin",
            ""
        )

        if not self.origin_allowed(
            origin
        ):
            self.send_response(403)
            self.send_header(
                "Content-Length",
                "0",
            )
            self.end_headers()
            return

        self.send_response(204)

        if origin:
            self.send_header(
                "Access-Control-Allow-Origin",
                origin,
            )
            self.send_header(
                "Vary",
                "Origin",
            )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS",
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )

        self.send_header(
            "Access-Control-Max-Age",
            "600",
        )

        self.send_header(
            "Content-Length",
            "0",
        )

        self.end_headers()

    def do_POST(self):
        origin = self.headers.get(
            "Origin",
            ""
        )

        if not self.post_allowed(
            origin
        ):
            self.send_json(
                {
                    "error":
                        "origin not allowed",
                },
                status=403,
            )
            return

        parsed = urllib.parse.urlparse(
            self.path
        )

        if parsed.path == "/check-updates":
            try:
                if not DOCKHAND_URL:
                    raise RuntimeError(
                        "DOCKHAND_URL not configured"
                    )

                endpoint = (
                    f"{DOCKHAND_URL}"
                    "/api/containers/check-updates?"
                    + urllib.parse.urlencode({
                        "env": DOCKHAND_ENV_ID,
                    })
                )

                request = urllib.request.Request(
                    endpoint,
                    data=b"",
                    headers={
                        "Accept":
                            "application/json",
                        "User-Agent":
                            "glance-docker-data/8.0",
                        "Origin":
                            DOCKHAND_URL,
                    },
                    method="POST",
                )

                try:
                    with urllib.request.urlopen(
                        request,
                        timeout=20,
                    ) as response:
                        response_body = (
                            response.read()
                        )

                        status_code = (
                            response.status
                        )

                except urllib.error.HTTPError as exc:
                    response_body = (
                        exc.read()
                    )

                    message = (
                        response_body.decode(
                            "utf-8",
                            errors="replace",
                        )
                        or str(exc)
                    )

                    print(
                        "[check-updates] "
                        "Dockhand error "
                        f"status={exc.code}: "
                        f"{message}",
                        flush=True,
                    )

                    self.send_json(
                        {
                            "error":
                                "Dockhand update check failed",
                            "status":
                                exc.code,
                            "detail":
                                message[:1000],
                        },
                        status=502,
                    )
                    return

                result = None

                if response_body:
                    try:
                        result = json.loads(
                            response_body
                        )
                    except Exception:
                        result = (
                            response_body.decode(
                                "utf-8",
                                errors="replace",
                            )
                        )

                print(
                    "[check-updates] requested "
                    f"dockhand_status={status_code}",
                    flush=True,
                )

                self.send_json({
                    "success": True,
                    "dockhand_status":
                        status_code,
                    "result":
                        result,
                })

            except Exception as exc:
                print(
                    "[check-updates] error: "
                    f"{exc}",
                    flush=True,
                )

                self.send_json(
                    {
                        "error": str(exc),
                    },
                    status=500,
                )

            return

        if parsed.path != "/redeploy-stack":
            self.send_json(
                {
                    "error": "not found",
                },
                status=404,
            )
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
                or 0
            )

            if length <= 0 or length > 4096:
                raise ValueError(
                    "invalid request body"
                )

            payload = json.loads(
                self.rfile.read(
                    length
                ).decode("utf-8")
            )

            stack_name = str(
                payload.get(
                    "stack",
                    ""
                )
            ).strip()

            if not stack_name:
                raise ValueError(
                    "stack is required"
                )

            action = str(
                payload.get(
                    "action",
                    "redeploy"
                )
            ).strip().lower()

            if action not in {
                "redeploy",
                "update",
            }:
                raise ValueError(
                    "action must be redeploy or update"
                )

            # Use the same live stack inventory that feeds Glance.
            data = docker_stack_data()

            stacks = {
                str(
                    stack.get(
                        "name",
                        ""
                    )
                ).lower():
                    str(
                        stack.get(
                            "name",
                            ""
                        )
                    )
                for stack in data.get(
                    "stacks",
                    []
                )
                if stack.get("name")
            }

            key = stack_name.lower()

            if key not in stacks:
                self.send_json(
                    {
                        "error":
                            "unknown stack",
                    },
                    status=404,
                )
                return

            actual_name = stacks[key]

            # Generic Dockhand redeploy cannot safely recreate
            # the Dockhand container that is running the operation.
            if is_dockhand_manager_name(actual_name):
                self.send_json(
                    {
                        "error":
                            "Dockhand cannot be redeployed "
                            "through the generic deploy endpoint",
                    },
                    status=409,
                )
                return

            if not DOCKHAND_URL:
                raise RuntimeError(
                    "DOCKHAND_URL not configured"
                )

            endpoint = (
                f"{DOCKHAND_URL}"
                f"/api/stacks/"
                f"{urllib.parse.quote(actual_name, safe='')}"
                f"/deploy?"
                + urllib.parse.urlencode({
                    "env": DOCKHAND_ENV_ID,
                })
            )

            body = json.dumps({
                "pull": action == "update",
                "build": False,
                "forceRecreate": True,
            }).encode("utf-8")

            request = urllib.request.Request(
                endpoint,
                data=body,
                headers={
                    "Content-Type":
                        "application/json",
                    "Accept":
                        "application/json",
                    "User-Agent":
                        "glance-docker-data/8.0",
                    "Origin":
                        DOCKHAND_URL,
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(
                    request,
                    timeout=120,
                ) as response:
                    response_body = (
                        response.read()
                    )

                    status_code = (
                        response.status
                    )

            except urllib.error.HTTPError as exc:
                response_body = (
                    exc.read()
                )

                message = (
                    response_body.decode(
                        "utf-8",
                        errors="replace",
                    )
                    or str(exc)
                )

                print(
                    "[redeploy] Dockhand error "
                    f"stack={actual_name} "
                    f"status={exc.code}: "
                    f"{message}",
                    flush=True,
                )

                self.send_json(
                    {
                        "error":
                            "Dockhand deploy failed",
                        "stack":
                            actual_name,
                        "status":
                            exc.code,
                        "detail":
                            message[:1000],
                    },
                    status=502,
                )
                return

            result = None

            if response_body:
                try:
                    result = json.loads(
                        response_body
                    )
                except Exception:
                    result = (
                        response_body.decode(
                            "utf-8",
                            errors="replace",
                        )
                    )

            if (
                isinstance(result, dict)
                and result.get("success") is False
            ):
                message = str(
                    result.get("error")
                    or "Dockhand deploy failed"
                )

                print(
                    "[redeploy] Dockhand deploy failed "
                    f"stack={actual_name}: "
                    f"{message}",
                    flush=True,
                )

                self.send_json(
                    {
                        "error":
                            "Dockhand deploy failed",
                        "stack":
                            actual_name,
                        "dockhand_status":
                            status_code,
                        "detail":
                            message[:1000],
                    },
                    status=502,
                )
                return

            print(
                "[redeploy] requested "
                f"stack={actual_name} "
                f"dockhand_status={status_code}",
                flush=True,
            )

            self.send_json({
                "success": True,
                "stack": actual_name,
                "dockhand_status":
                    status_code,
                "result": result,
            })

        except (
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            self.send_json(
                {
                    "error": str(exc),
                },
                status=400,
            )

        except Exception as exc:
            print(
                "[redeploy] error: "
                f"{exc}",
                flush=True,
            )

            self.send_json(
                {
                    "error": str(exc),
                },
                status=500,
            )

    def do_GET(self):
        if (
            self.path
            == "/health/tailscale"
        ):
            metrics = tailscale_metrics()

            connected = bool(
                metrics.get(
                    "connected"
                )
            )

            self.send_json(
                {
                    "status":
                        "connected"
                        if connected
                        else "disconnected",

                    "connected":
                        connected,

                    "backend_state":
                        metrics.get(
                            "backend_state",
                            "",
                        ),

                    "self_online":
                        metrics.get(
                            "self_online",
                            False,
                        ),

                    "ipv4":
                        metrics.get(
                            "ipv4",
                            "",
                        ),
                },
                status=
                    200
                    if connected
                    else 503,
            )

            return

        if (
            self.path
            == "/health"
        ):
            try:
                containers = docker_request(
                    "/containers/json?all=true"
                )

                ensure_catalog()

                overrides = (
                    load_overrides()
                )

                self.send_json({
                    "status":
                        "ok",

                    "docker":
                        "connected",

                    "containers":
                        len(
                            containers
                        ),

                    "dockhand":
                        bool(
                            DOCKHAND_URL
                        ),

                    "dockhand_env":
                        DOCKHAND_ENV_ID,

                    "selfhst_catalog":
                        bool(
                            catalog_cache[
                                "index"
                            ]
                        ),

                    "catalog_projects":
                        len(
                            catalog_cache[
                                "projects"
                            ]
                        ),

                    "catalog_error":
                        catalog_cache[
                            "error"
                        ],

                    "overrides_file":
                        OVERRIDES_FILE,

                    "overrides_error":
                        overrides[
                            "error"
                        ],

                    "override_groups":
                        len(
                            overrides[
                                "groups"
                            ]
                        ),

                    "override_names":
                        len(
                            overrides[
                                "names"
                            ]
                        ),

                    "override_icons":
                        len(
                            overrides[
                                "icons"
                            ]
                        ),

                    "override_portals":
                        len(
                            overrides[
                                "portals"
                            ]
                        ),
                })

            except Exception as exc:
                self.send_json({
                    "status":
                        "error",

                    "error":
                        str(
                            exc
                        ),
                })

            return


        if (
            self.path
            == "/truenas-metrics"
        ):
            try:
                self.send_json(
                    truenas_metrics()
                )

            except Exception as exc:
                print(
                    "truenas-metrics error: "
                    f"{exc}",
                    flush=True,
                )

                self.send_json(
                    {
                        "error":
                            str(exc),
                    },
                    status=500,
                )

            return

        if (
            self.path
            == "/home-metrics"
        ):
            try:
                self.send_json(
                    home_metrics()
                )

            except Exception as exc:
                print(
                    "home-metrics error: "
                    f"{exc}",
                    flush=True,
                )

                self.send_json(
                    {
                        "error":
                            str(exc),
                    },
                    status=500,
                )

            return

        if (
            self.path
            == "/docker-stacks"
        ):
            try:
                self.send_json(
                    docker_stack_data()
                )

            except Exception as exc:
                print(
                    "docker-data error: "
                    f"{exc}",
                    flush=True,
                )

                self.send_json({
                    "error":
                        str(
                            exc
                        ),

                    "groups":
                        [],

                    "stacks":
                        [],
                })

            return

        self.send_json(
            {
                "error":
                    "not found"
            },
            status=404,
        )

    def log_message(
        self,
        fmt,
        *args
    ):
        return


# =============================================================================
# START
# =============================================================================

def catalog_background_start():
    try:
        ensure_catalog()

    except Exception as exc:
        print(
            "catalog startup error: "
            f"{exc}",
            flush=True,
        )


load_overrides()

print(
    "docker-data listening on :8080 "
    "(Docker + Dockhand + metadata + automatic portals)",
    flush=True,
)

threading.Thread(
    target=catalog_background_start,
    daemon=True,
).start()

DualStackThreadingHTTPServer(
    (
        "::",
        8080,
    ),
    Handler,
).serve_forever()
