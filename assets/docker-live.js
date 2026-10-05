(() => {
  "use strict";

  const POLL_MS = 5000;
  const LIVE_FETCH_TIMEOUT_MS = 12_000;
  const ACTION_FETCH_TIMEOUT_MS = 130_000;
  const DOCKER_DATA_PORT = Number(
    window.GLANCE_DOCKER_DATA_PORT || 30083
  );
  const DOCKER_DATA_BASE_URL = String(
    window.GLANCE_DOCKER_DATA_URL || ""
  ).replace(/\/+$/, "");

  /*
   * Service details are rendered only here from the same /docker-stacks
   * payload used for generic Docker state. docker.yml owns card structure and
   * layout; this file is the single source of truth for service-detail markup.
   */

  function intValue(value) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.trunc(number) : 0;
  }

  function floatValue(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
  }

  function plural(value, singular, pluralForm = `${singular}s`) {
    return intValue(value) === 1 ? singular : pluralForm;
  }

  function detailsBlock(
    marginTop = 4,
    extraClass = "",
    lineHeight = ""
  ) {
    const el = document.createElement("div");
    el.className = `size-h6${extraClass ? ` ${extraClass}` : ""}`;
    el.setAttribute("data-service-details", "");
    el.style.marginLeft = "31px";
    el.style.marginTop = `${marginTop}px`;
    if (lineHeight) {
      el.style.lineHeight = lineHeight;
    }
    return el;
  }

  function child(tag, text = "", className = "", style = "") {
    const el = document.createElement(tag);
    if (className) {
      el.className = className;
    }
    if (style) {
      el.style.cssText = style;
    }
    if (text !== null && text !== undefined) {
      el.textContent = String(text);
    }
    return el;
  }

  function unavailableDetails(message, marginTop = 4) {
    const details = detailsBlock(marginTop, "color-negative");
    details.textContent = message;
    return details;
  }

  function serviceStatusSpan(service) {
    const level = String(service?.status_level || "");
    const span = child("span", service?.status_text || "UNKNOWN");

    if (level === "critical") {
      span.className = "color-negative";
    } else if (level === "warning") {
      span.style.color = "var(--color-primary)";
    } else {
      span.className = "color-positive";
    }

    return span;
  }


  function formatBrowserDate(timestamp, fallback = "") {
    const seconds = Number(timestamp);

    if (!Number.isFinite(seconds)) {
      return fallback;
    }

    const date = new Date(seconds * 1000);

    if (Number.isNaN(date.getTime())) {
      return fallback;
    }

    return new Intl.DateTimeFormat(
      undefined,
      {
        weekday: "short",
        day: "numeric",
      }
    ).format(date);
  }

  function renderArrDetails(service, type) {
    const marginTop = 5;
    const label = type === "sonarr" ? "Sonarr" : "Radarr";

    if (!service.available) {
      return unavailableDetails(`${label} API unavailable`, 3);
    }

    const details = detailsBlock(marginTop);
    const summary = child(
      "div",
      null,
      "",
      "display:flex;gap:14px;align-items:center;white-space:nowrap;"
    );

    summary.appendChild(child("span", `Queue ${intValue(service.queue)}`));
    summary.appendChild(child("span", `Missing ${intValue(service.missing)}`));

    summary.appendChild(
      child(
        "span",
        service.healthy
          ? "✓ Healthy"
          : `${intValue(service.health_issues)} issue(s)`,
        service.healthy ? "color-positive" : "color-negative"
      )
    );
    details.appendChild(summary);

    const upcoming = (
      Array.isArray(service.upcoming)
        ? service.upcoming
        : []
    ).filter(item => {
      const timestamp = Number(item?.timestamp);

      /*
       * The backend supplies absolute timestamps. Determine whether an
       * event is still upcoming in the browser rather than using the
       * server's calendar date/timezone.
       *
       * Keep entries without a usable timestamp so their backend date
       * remains available as a fallback.
       */
      return (
        !Number.isFinite(timestamp) ||
        timestamp > Date.now() / 1000
      );
    });
    if (!upcoming.length) {
      details.appendChild(
        child(
          "div",
          type === "sonarr"
            ? "No monitored episodes in the next 7 days"
            : "No monitored movies in the next 7 days",
          "color-subdue",
          "margin-top:8px;"
        )
      );
      return details;
    }

    details.appendChild(
      child(
        "div",
        type === "sonarr" ? "Upcoming TV" : "Upcoming Movies",
        "color-subdue",
        "text-transform:uppercase;letter-spacing:0.08em;margin-top:10px;margin-bottom:4px;"
      )
    );

    for (const item of upcoming) {
      const row = child(
        "div",
        null,
        "",
        "display:grid;grid-template-columns:48px minmax(0,1fr) auto;gap:8px;align-items:center;margin-top:4px;"
      );
      row.appendChild(
        child(
          "span",
          formatBrowserDate(
            item?.timestamp,
            item?.date || ""
          ),
          "color-subdue",
          "white-space:nowrap;"
        )
      );

      const title = child("span", item?.title || "", "text-truncate color-highlight");
      title.title = item?.title || "";
      row.appendChild(title);

      row.appendChild(
        child(
          "span",
          type === "sonarr" ? item?.episode || "" : item?.release_type || "",
          "color-subdue",
          "white-space:nowrap;"
        )
      );
      details.appendChild(row);
    }

    return details;
  }

  const warnedServiceTypes = new Set();

  function renderQbittorrentDetails(service) {
    if (!service.available) {
      return unavailableDetails("qBit API unavailable", 3);
    }

    const details = detailsBlock(4);
    const rates = child("div", null, "", "display:flex;gap:12px;white-space:nowrap;");
    rates.appendChild(child("span", `↓ ${floatValue(service.download_mib).toFixed(1)} MiB/s`));
    rates.appendChild(child("span", `↑ ${floatValue(service.upload_mib).toFixed(1)} MiB/s`));
    details.appendChild(rates);
    details.appendChild(
      child(
        "div",
        `${intValue(service.total)} total · ${intValue(service.downloading)} downloading · ${intValue(service.active_seeds)} uploading`,
        "color-subdue",
        "margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
      )
    );
    if (intValue(service.errors) > 0) {
      details.appendChild(
        child("div", `${intValue(service.errors)} torrent error(s)`, "color-negative", "margin-top:2px;")
      );
    }
    return details;
  }

  function renderSportarrDetails(service) {
    if (!service.available) {
      return unavailableDetails("Sportarr API unavailable", 5);
    }

    const details = detailsBlock(5);
    const upcoming = (
      Array.isArray(service.upcoming)
        ? service.upcoming
        : []
    ).filter(item => {
      const timestamp = Number(item?.timestamp);

      /*
       * The backend supplies absolute timestamps. Determine whether an
       * event is still upcoming in the browser rather than using the
       * server's calendar date/timezone.
       *
       * Keep entries without a usable timestamp so their backend date
       * remains available as a fallback.
       */
      return (
        !Number.isFinite(timestamp) ||
        timestamp > Date.now() / 1000
      );
    });
    if (!upcoming.length) {
      details.appendChild(
        child("div", "No monitored sporting events in the next 7 days", "color-subdue", "margin-top:7px;")
      );
      return details;
    }

    details.appendChild(
      child(
        "div",
        "Upcoming Sports",
        "color-subdue",
        "text-transform:uppercase;letter-spacing:0.08em;margin-top:7px;margin-bottom:5px;"
      )
    );

    for (const item of upcoming) {
      const row = child(
        "div",
        null,
        "",
        "display:grid;grid-template-columns:56px minmax(0,1fr) auto;gap:10px;align-items:center;margin-top:5px;"
      );
      row.appendChild(
        child(
          "span",
          formatBrowserDate(
            item?.timestamp,
            item?.date || ""
          ),
          "color-subdue",
          "white-space:nowrap;"
        )
      );
      const title = child("span", item?.title || "", "text-truncate color-highlight", "min-width:0;");
      title.title = item?.title || "";
      row.appendChild(title);
      const meta = item?.league || item?.sport || "";
      if (meta) {
        row.appendChild(child("span", meta, "color-subdue", "white-space:nowrap;"));
      }
      details.appendChild(row);
    }

    const count = intValue(service.upcoming_count);
    if (count > 6) {
      details.appendChild(child("div", `+${count - 6} more`, "color-subdue", "margin-top:6px;"));
    }
    return details;
  }

  function renderPeanutDetails(service) {
    if (!service.available) {
      return unavailableDetails("UPS data unavailable", 5);
    }

    const details = detailsBlock(5, "", "1.45");
    const first = child("div", null);
    first.appendChild(serviceStatusSpan(service));
    let battery = ` · ${intValue(service.battery_charge)}% battery`;
    if (service.runtime_text) {
      battery += ` · ${service.runtime_text} runtime`;
    }
    first.appendChild(child("span", battery, "color-subdue"));
    details.appendChild(first);

    let load = `${intValue(service.load_percent)}% load`;
    if (intValue(service.load_watts) > 0) {
      load += ` · ~${intValue(service.load_watts)} W`;
    }
    load += ` · ${floatValue(service.input_voltage).toFixed(0)} V`;
    details.appendChild(child("div", load, "color-subdue"));
    return details;
  }

  function renderTailscaleDetails(service) {
    if (!service.available) {
      return unavailableDetails("Tailscale status unavailable", 5);
    }

    const details = detailsBlock(5, "", "1.45");
    const first = child("div", null);
    first.appendChild(serviceStatusSpan(service));
    details.appendChild(first);
    const peers = intValue(service.peers_online);
    details.appendChild(
      child("div", `${service.ipv4 || ""} · ${peers} ${plural(peers, "peer")} online`, "color-subdue")
    );
    return details;
  }

  function renderBeszelDetails(service) {
    if (!service.available) {
      return unavailableDetails("Beszel API unavailable", 4);
    }

    const details = detailsBlock(4, "", "1.45");
    const alertsAvailable = service.alerts_available === true;
    const alertCount = intValue(service.alert_count);
    const uptime = service.uptime_text || "—";

    if (!alertsAvailable) {
      details.appendChild(
        child("div", "⚠ Alerts unavailable", "color-negative")
      );
      details.appendChild(
        child(
          "div",
          `CPU ${floatValue(service.cpu).toFixed(0)}% · RAM ${floatValue(service.memory).toFixed(0)}% · Up ${uptime}`,
          "color-subdue"
        )
      );
      return details;
    }

    if (alertCount > 0) {
      details.appendChild(
        child(
          "div",
          `⚠ ${alertCount} active ${plural(alertCount, "alert")}`,
          "color-negative"
        )
      );

      for (const alert of Array.isArray(service.alerts) ? service.alerts : []) {
        details.appendChild(
          child("div", alert?.text || "Alert", "color-negative")
        );
      }

      details.appendChild(child("div", `Up ${uptime}`, "color-subdue"));
      return details;
    }

    details.appendChild(
      child("div", "✓ Healthy · 0 alerts", "color-positive")
    );
    details.appendChild(
      child(
        "div",
        `CPU ${floatValue(service.cpu).toFixed(0)}% · RAM ${floatValue(service.memory).toFixed(0)}% · Up ${uptime}`,
        "color-subdue"
      )
    );
    return details;
  }

  function renderSubscribarrDetails(service) {
    if (!service.available) {
      return unavailableDetails(
        "Subscribarr API unavailable",
        4
      );
    }

    const details = detailsBlock(
      4,
      "",
      "1.45"
    );

    const status = child(
      "div",
      null
    );

    status.appendChild(
      serviceStatusSpan(service)
    );

    status.appendChild(
      child(
        "span",
        ` · ${intValue(service.shows)} ${plural(service.shows, "show")}`,
        "color-subdue"
      )
    );

    details.appendChild(status);

    details.appendChild(
      child(
        "div",
        `${intValue(service.library)} episodes · ${intValue(service.missing)} missing`,
        "color-subdue"
      )
    );

    const failed = intValue(
      service.failed
    );

    const unmatched = intValue(
      service.unmatched
    );

    let issues =
      `${unmatched} unmatched · ${failed} failed`;

    if (service.youtube_paused) {
      issues += " · YouTube API paused";
    }

    details.appendChild(
      child(
        "div",
        issues,
        failed > 0
          ? "color-negative"
          : "color-subdue"
      )
    );

    return details;
  }


  function renderPaperlessDetails(service) {
    if (!service.available) {
      return unavailableDetails("Paperless API unavailable", 4);
    }
    const details = detailsBlock(4, "", "1.45");
    details.appendChild(child("div", `${intValue(service.documents)} documents · ${intValue(service.inbox)} inbox`));
    details.appendChild(
      child(
        "div",
        `${intValue(service.correspondents)} correspondents · ${intValue(service.document_types)} types · ${intValue(service.tags)} tags`,
        "color-subdue"
      )
    );
    return details;
  }

  function renderDispatcharrDetails(service) {
    if (!service.available) {
      return unavailableDetails("Dispatcharr API unavailable", 4);
    }
    const details = detailsBlock(4, "", "1.45");
    details.appendChild(
      child(
        "div",
        `${intValue(service.local_connections)} local · ${intValue(service.provider_connections)} provider`,
        "color-subdue"
      )
    );
    return details;
  }

  function renderImmichDetails(service) {
    if (!service.available) {
      return unavailableDetails("Immich API unavailable", 4);
    }
    const details = detailsBlock(4, "", "1.45");
    details.appendChild(
      child(
        "div",
        `${intValue(service.photos).toLocaleString()} photos · ${intValue(service.videos).toLocaleString()} videos · ${(intValue(service.usage) / (1024 ** 4)).toFixed(1)} TiB`
      )
    );
    const failed = intValue(service.failed_jobs);
    details.appendChild(
      child(
        "div",
        failed > 0 ? `⚠ ${failed} failed jobs` : "✓ No failed jobs",
        failed > 0 ? "color-negative" : "color-positive"
      )
    );
    return details;
  }

  function renderJellyfinDetails(service) {
    if (!service.available) {
      return unavailableDetails("Jellyfin API unavailable", 4);
    }
    const details = detailsBlock(4, "", "1.45");
    const streams = intValue(service.streams);
    const transcodes = intValue(service.transcodes);
    const summary = child("div", null);
    summary.appendChild(child("span", `${streams} ${plural(streams, "stream")}`));
    if (transcodes > 0) {
      summary.appendChild(child("span", ` · ${transcodes} ${plural(transcodes, "transcode")}`, "", "color:#e5c07b;"));
    }
    details.appendChild(summary);

    for (const item of Array.isArray(service.active_streams) ? service.active_streams : []) {
      const text = `${item?.title || ""}${item?.subtitle ? ` · ${item.subtitle}` : ""}`;
      const row = child("div", text, "color-subdue text-truncate", "margin-top:2px;");
      row.title = item?.title || "";
      details.appendChild(row);
    }
    return details;
  }

  function renderProwlarrDetails(service) {
    if (!service.available) {
      return unavailableDetails("Prowlarr API unavailable", 4);
    }
    const details = detailsBlock(4);
    if (service.healthy) {
      details.appendChild(
        child("span", `✓ ${intValue(service.healthy_count)}/${intValue(service.total)} indexers healthy`, "color-positive")
      );
    } else {
      let text = `⚠ ${intValue(service.failed)} indexer failures`;
      if (intValue(service.health_issues) > 0) {
        text += ` · ${intValue(service.health_issues)} health issues`;
      }
      details.appendChild(child("span", text, "color-negative"));
    }
    return details;
  }

  function renderBazarrDetails(service) {
    if (!service.available) {
      return unavailableDetails("Bazarr API unavailable", 4);
    }
    const details = detailsBlock(4, "", "1.45");
    const episodes = intValue(service.wanted_episodes);
    const movies = intValue(service.wanted_movies);
    details.appendChild(
      child(
        "div",
        `${episodes} ${plural(episodes, "episode")} · ${movies} ${plural(movies, "movie")} missing`
      )
    );
    const issues = intValue(service.provider_issues);
    details.appendChild(
      child(
        "div",
        issues > 0
          ? `⚠ ${issues} provider ${plural(issues, "issue")}`
          : `✓ ${intValue(service.providers_good)}/${intValue(service.providers)} providers healthy`,
        issues > 0 ? "color-negative" : "color-positive"
      )
    );
    return details;
  }

  function renderUptimeKumaDetails(service) {
    if (!service.available) {
      return unavailableDetails("Uptime Kuma API unavailable", 4);
    }
    const details = detailsBlock(4, "", "1.45");
    const status = child(
      "div",
      `${service.healthy ? "✓" : "⚠"} ${intValue(service.up)}/${intValue(service.total)} monitors up`,
      service.healthy ? "color-positive" : "color-negative"
    );
    details.appendChild(status);
    if (!service.healthy && service.problem_names) {
      details.appendChild(child("div", service.problem_names, "color-negative"));
    }
    details.appendChild(child("div", `${floatValue(service.uptime_24h)}% 24h uptime`, "color-subdue"));
    return details;
  }

  function renderGatusDetails(service) {
    if (!service.available) {
      return unavailableDetails("Gatus API unavailable", 4);
    }

    const details = detailsBlock(4, "", "1.45");
    const healthy = service.healthy === true;
    const up = intValue(service.up);
    const total = intValue(service.total);

    details.appendChild(
      child(
        "div",
        `${healthy ? "✓" : "⚠"} ${up}/${total} endpoints up`,
        healthy ? "color-positive" : "color-negative"
      )
    );

    if (!healthy && service.problem_names) {
      details.appendChild(
        child("div", service.problem_names, "color-negative")
      );
    }

    const avg = floatValue(service.average_response_ms);
    const slowest = floatValue(service.slowest_response_ms);

    let summary = `Avg ${avg.toFixed(0)} ms`;

    if (service.slowest_name && slowest > 0) {
      summary += ` · Slowest ${service.slowest_name} ${slowest.toFixed(0)} ms`;
    }

    details.appendChild(
      child("div", summary, "color-subdue")
    );

    return details;
  }

  function renderTdarrDetails(service) {
    if (!service.available) {
      return unavailableDetails("Tdarr API unavailable", 4);
    }
    const details = detailsBlock(4, "", "1.45");
    const processing = intValue(service.processing);
    const first = child("div", null);
    if (processing > 0) {
      first.appendChild(document.createTextNode(`${processing} processing`));
    } else {
      first.appendChild(child("span", "Idle", "color-positive"));
    }
    first.appendChild(document.createTextNode(` · ${intValue(service.queued)} queued`));
    details.appendChild(first);
    details.appendChild(
      child(
        "div",
        `${intValue(service.nodes_online)}/${intValue(service.nodes)} nodes online · ${intValue(service.workers)} workers`,
        "color-subdue"
      )
    );
    return details;
  }

  function renderStorageHistoryDetails(service) {
    if (!service.available) {
      const details = child(
        "div",
        "Storage history unavailable",
        "size-h6 color-subdue",
        "margin-left:31px;margin-top:4px;"
      );

      details.setAttribute(
        "data-service-details",
        ""
      );

      return details;
    }

    const datasets =
      service.datasets || {};

    const sata =
      datasets["SATA_16TB"] || {};

    const video =
      datasets["SATA_16TB/Video"] || {};

    const pictures =
      datasets["SATA_16TB/Pictures"] || {};

    const nvme =
      datasets["NVME_4TB"] || {};

    const tmp =
      datasets["NVME_TMP"] || {};

    const delta = (item, period) =>
      item?.change_text?.[period] || "";

    const root = child(
      "div",
      "",
      "size-h6",
      "margin-left:31px;"
        + "margin-top:4px;"
        + "line-height:1.45;"
    );

    root.setAttribute(
      "data-service-details",
      ""
    );

    const appendSubdue = (row, text) => {
      row.appendChild(
        child(
          "span",
          text,
          "color-subdue"
        )
      );
    };

    const sataRow = child(
      "div",
      `SATA ${delta(sata, "7d")} `
    );

    appendSubdue(
      sataRow,
      "7d ·"
    );

    sataRow.appendChild(
      document.createTextNode(
        ` ${delta(sata, "30d")} `
      )
    );

    appendSubdue(
      sataRow,
      "30d"
    );

    root.appendChild(sataRow);

    const mediaRow = child(
      "div",
      `Video ${delta(video, "7d")} `
    );

    appendSubdue(
      mediaRow,
      "7d ·"
    );

    mediaRow.appendChild(
      document.createTextNode(
        ` Pictures ${delta(pictures, "7d")} `
      )
    );

    appendSubdue(
      mediaRow,
      "7d"
    );

    root.appendChild(mediaRow);

    const nvmeRow = child(
      "div",
      `NVME ${delta(nvme, "7d")} `
    );

    appendSubdue(
      nvmeRow,
      "7d ·"
    );

    nvmeRow.appendChild(
      document.createTextNode(
        ` TMP ${delta(tmp, "7d")} `
      )
    );

    appendSubdue(
      nvmeRow,
      "7d"
    );

    root.appendChild(nvmeRow);

    return root;
  }

  function renderScrutinyDetails(service) {
    if (!service.available) {
      return unavailableDetails("SMART data unavailable", 4);
    }

    const warnings = intValue(service.warnings);
    const drives = intValue(service.drives);
    const maxTemp = intValue(service.max_temp);
    const details = detailsBlock(4);

    if (warnings > 0) {
      details.appendChild(
        child(
          "div",
          `⚠ ${warnings} drive ${plural(warnings, "warning")}`,
          "color-negative"
        )
      );
    } else {
      details.appendChild(
        child(
          "div",
          `✓ ${drives} ${plural(drives, "drive")} healthy`,
          "color-positive"
        )
      );
    }

    if (maxTemp > 0) {
      details.appendChild(
        child(
          "div",
          `Max temp ${maxTemp}°C`,
          "color-subdue"
        )
      );
    }

    return details;
  }

  function renderPlexDetails(service) {
    if (!service.available) {
      return unavailableDetails("Tautulli API unavailable", 3);
    }

    const details = detailsBlock(4);
    const streams = intValue(service.streams);
    const summary = child("div", null, "", "display:flex;gap:12px;white-space:nowrap;");
    summary.appendChild(child("span", `${streams} ${plural(streams, "stream")}`));
    if (intValue(service.direct_play) > 0) {
      summary.appendChild(child("span", `${intValue(service.direct_play)} direct`, "color-positive"));
    }
    if (intValue(service.direct_stream) > 0) {
      summary.appendChild(child("span", `${intValue(service.direct_stream)} direct stream`, "color-positive"));
    }
    if (intValue(service.transcode) > 0) {
      summary.appendChild(child("span", `${intValue(service.transcode)} transcode`, "", "color:#e5c07b;"));
    }
    details.appendChild(summary);

    for (const item of Array.isArray(service.active_streams) ? service.active_streams : []) {
      const stream = child(
        "div",
        null,
        "",
        "margin-top:6px;padding-top:6px;border-top:1px solid var(--color-separator);min-width:0;"
      );
      const heading = child(
        "div",
        null,
        "",
        "display:flex;justify-content:space-between;gap:10px;min-width:0;"
      );
      const title = child("span", item?.title || "", "text-truncate color-highlight", "min-width:0;font-weight:600;");
      title.title = item?.title || "";
      heading.appendChild(title);

      const method = String(item?.method || "");
      const methodSpan = child(
        "span",
        method,
        method === "TRANSCODE" ? "" : "color-positive",
        `white-space:nowrap;flex:none;font-weight:600;${method === "TRANSCODE" ? "color:#e5c07b;" : ""}`
      );
      heading.appendChild(methodSpan);
      stream.appendChild(heading);

      if (item?.subtitle) {
        const subtitle = child(
          "div",
          item.subtitle,
          "color-subdue text-truncate",
          "margin-top:2px;min-width:0;"
        );
        subtitle.title = item.subtitle;
        stream.appendChild(subtitle);
      }

      let footer = item?.user || "";
      const bandwidth = floatValue(item?.bandwidth_mbps);
      if (footer && bandwidth > 0) {
        footer += " · ";
      }
      if (bandwidth > 0) {
        footer += `${bandwidth.toFixed(1)} Mbps`;
      }
      stream.appendChild(child("div", footer, "color-subdue", "margin-top:2px;white-space:nowrap;"));
      details.appendChild(stream);
    }
    return details;
  }

  const SERVICE_RENDERERS = {
    qbittorrent: renderQbittorrentDetails,
    sonarr: (service) => renderArrDetails(service, "sonarr"),
    radarr: (service) => renderArrDetails(service, "radarr"),
    sportarr: renderSportarrDetails,
    peanut: renderPeanutDetails,
    tailscale: renderTailscaleDetails,
    beszel: renderBeszelDetails,
    paperless: renderPaperlessDetails,
    subscribarr: renderSubscribarrDetails,
    dispatcharr: renderDispatcharrDetails,
    immich: renderImmichDetails,
    jellyfin: renderJellyfinDetails,
    prowlarr: renderProwlarrDetails,
    bazarr: renderBazarrDetails,
    "uptime-kuma": renderUptimeKumaDetails,
    gatus: renderGatusDetails,
    tdarr: renderTdarrDetails,
    "storage-history": renderStorageHistoryDetails,
    scrutiny: renderScrutinyDetails,
    plex: renderPlexDetails,
  };

  function renderServiceDetails(stack) {
    const service = stack?.service || {};
    const type = String(service.type || "").toLowerCase();

    if (!type || type === "dockhand") {
      return undefined;
    }

    const renderer = SERVICE_RENDERERS[type];
    if (renderer) {
      return renderer(service);
    }

    if (!warnedServiceTypes.has(type)) {
      warnedServiceTypes.add(type);
      console.warn(`[Docker Live] No renderer for service type: ${type}`);
    }
    return undefined;
  }

  function updateServiceDetails(stack) {
    const displayName = stack?.display_name || stack?.name;
    const card = cardFor(displayName);
    if (!card) {
      return;
    }

    const rendered = renderServiceDetails(stack);
    if (rendered === undefined) {
      return;
    }

    const current = card.querySelector(":scope > [data-service-details]");

    if (rendered === null) {
      current?.remove();
      return;
    }

    if (current) {
      current.replaceWith(rendered);
    } else {
      card.appendChild(rendered);
    }
  }

  async function fetchWithTimeout(
    url,
    options = {},
    timeoutMs = LIVE_FETCH_TIMEOUT_MS
  ) {
    const controller = new AbortController();

    const timeout = window.setTimeout(
      () => controller.abort(),
      timeoutMs
    );

    try {
      return await fetch(
        url,
        {
          ...options,
          signal: controller.signal
        }
      );
    } finally {
      window.clearTimeout(timeout);
    }
  }

  function helperUrl() {
    const base =
      DOCKER_DATA_BASE_URL ||
      `${location.protocol}//${location.hostname}:${DOCKER_DATA_PORT}`;

    return `${base}/docker-stacks`;
  }

  function cardFor(name) {
    return document.querySelector(
      `[data-docker-stack="${CSS.escape(name)}"]`
    );
  }

  function make(tag, text = null, style = "") {
    const el = document.createElement(tag);

    if (text !== null && text !== undefined) {
      el.textContent = text;
    }

    if (style) {
      el.style.cssText = style;
    }

    return el;
  }

  // ============================================================
  // DOCKER STACK REDEPLOY
  // ============================================================

  const REDEPLOY_EXCLUDED = new Set([
    "dockhand",
    "ix-dockhand",
    "glance",
    "glance-dashboard",
    "docker-data",
    "glance-docker-data"
  ]);

  function redeployUrl() {
    const base =
      DOCKER_DATA_BASE_URL ||
      `${location.protocol}//${location.hostname}:${DOCKER_DATA_PORT}`;

    return `${base}/redeploy-stack`;
  }

  function scheduleTransientPoll(delay) {
    window.GlanceLive.refreshLater(
      "docker",
      delay,
      "docker-action"
    );
  }

  function checkUpdatesUrl() {
    const base =
      DOCKER_DATA_BASE_URL ||
      `${location.protocol}//${location.hostname}:${DOCKER_DATA_PORT}`;

    return `${base}/check-updates`;
  }

  async function checkDockerUpdates(button) {
    if (
      !button ||
      button.dataset.busy === "true"
    ) {
      return;
    }

    const originalText =
      button.textContent;

    const originalTitle =
      button.title;

    button.dataset.busy = "true";
    button.textContent = "…";
    button.title = "Checking for app updates…";
    button.style.opacity = "0.55";
    button.style.pointerEvents = "none";

    try {
      const response = await fetchWithTimeout(
        checkUpdatesUrl(),
        {
          method: "POST",
          cache: "no-store"
        },
        30_000
      );

      let result = {};

      try {
        result = await response.json();
      } catch (_) {
        // HTTP status remains useful.
      }

      if (!response.ok) {
        throw new Error(
          result?.error ||
          `HTTP ${response.status}`
        );
      }

      button.textContent = "✓";
      button.title =
        "Update check started";

      /*
       * Dockhand's scan is asynchronous. Refresh several times
       * during the likely completion window; normal 15-second
       * polling remains the eventual fallback.
       */
      for (const delay of [
        2000,
        5000,
        10000
      ]) {
        scheduleTransientPoll(delay);
      }

      window.setTimeout(
        () => {
          if (button.isConnected) {
            button.textContent =
              originalText;


            button.title =
              originalTitle;
          }
        },
        2500
      );

    } catch (error) {
      console.error(
        "[Docker Live] Check updates failed:",
        error
      );

      button.textContent = "!";
      button.title =
        `Check updates failed: ${error.message}`;

      window.setTimeout(
        () => {
          if (button.isConnected) {
            button.textContent =
              originalText;

            button.title =
              originalTitle;
          }
        },
        4000
      );

    } finally {
      button.dataset.busy = "false";
      button.style.opacity = "";
      button.style.pointerEvents = "";
    }
  }


  async function redeployStack(
    stack,
    button,
    action = "redeploy",
    options = {}
  ) {
    const name =
      String(stack?.name || "").trim();

    if (
      !name ||
      REDEPLOY_EXCLUDED.has(
        name.toLowerCase()
      ) ||
      button.dataset.busy === "true"
    ) {
      return;
    }

    const originalText =
      button.textContent;

    button.dataset.busy = "true";
    button.textContent = "⟳";
    button.title =
      action === "update"
        ? `Updating ${name}…`
        : `Redeploying ${name}…`;
    button.style.opacity = "0.55";
    button.style.pointerEvents = "none";

    try {
      const response = await fetchWithTimeout(
        redeployUrl(),
        {
          method: "POST",
          cache: "no-store",
          headers: {
            "Content-Type":
              "application/json"
          },
          body: JSON.stringify({
            stack: name,
            action
          })
        },
        ACTION_FETCH_TIMEOUT_MS
      );

      let result = {};

      try {
        result = await response.json();
      } catch (_) {
        // Keep the HTTP status as the useful error.
      }

      if (!response.ok) {
        throw new Error(
          result?.error ||
          `HTTP ${response.status}`
        );
      }

      button.textContent = "✓";
      button.title =
        action === "update"
          ? `${name} updated`
          : `${name} redeployed`;

      /*
       * Give Docker a moment to settle, then refresh the
       * generic card state/service data immediately instead
       * of waiting for the next 15-second interval.
       */
      if (!options.suppressPoll) {
        scheduleTransientPoll(1500);
      }

      window.setTimeout(
        () => {
          button.textContent =
            originalText;

          button.title =
            action === "update"
              ? `Update ${name}`
              : `Redeploy ${name}`;
        },
        2500
      );

      return true;

    } catch (error) {
      console.error(
        `[Docker Live] ${action} failed for ${name}:`,
        error
      );

      button.textContent = "!";
      button.title =
        `${action === "update" ? "Update" : "Redeploy"} failed: ${error.message}`;

      window.setTimeout(
        () => {
          button.textContent =
            originalText;

          button.title =
            action === "update"
              ? `Update ${name}`
              : `Redeploy ${name}`;
        },
        4000
      );

      return false;

    } finally {
      button.dataset.busy = "false";
      button.style.opacity = "";
      button.style.pointerEvents = "";
    }
  }

  /*
   * DOCKHAND CHECK-UPDATES CONTROL
   *
   * Delegated because Glance may insert the Docker custom-api
   * cards after this script has already started.
   */
  document.addEventListener(
    "click",
    event => {
      const button =
        event.target.closest(
          ".docker-check-updates"
        );

      if (!button) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      checkDockerUpdates(button);
    }
  );


  // ============================================================
  // DOCKHAND UPDATE ALL
  // ============================================================

  async function updateAllStacks(button) {
    if (
      !button ||
      button.dataset.busy === "true"
    ) {
      return;
    }

    const originalText = button.textContent.trim();

    button.dataset.busy = "true";
    button.textContent = "Updating apps…";
    button.style.opacity = "0.55";
    button.style.pointerEvents = "none";

    const failures = [];

    try {
      /*
       * Fetch a fresh stack list at click time rather than trusting
       * the count rendered into the Dockhand card.
       */
      const response = await fetchWithTimeout(
        helperUrl(),
        {
          cache: "no-store"
        },
        LIVE_FETCH_TIMEOUT_MS
      );

      if (!response.ok) {
        throw new Error(
          `docker-data returned HTTP ${response.status}`
        );
      }

      const data = await response.json();

      if (!Array.isArray(data.stacks)) {
        throw new Error(
          "docker-data response has no stacks array"
        );
      }

      const eligible = data.stacks.filter(
        stack =>
          Boolean(stack.update_available) &&
          !REDEPLOY_EXCLUDED.has(
            String(stack.name || "").toLowerCase()
          )
      );

      if (!eligible.length) {
        button.textContent = "✓ All apps current";

        scheduleTransientPoll(500);

        return;
      }

      let completed = 0;

      for (const stack of eligible) {
        completed += 1;

        button.textContent =
          `Updating ${completed}/${eligible.length}…`;

        const card = [...document.querySelectorAll(
          "[data-docker-stack]"
        )].find(
          el =>
            String(
              el.dataset.dockerStack || ""
            ).toLowerCase() ===
            String(
              stack.display_name ||
              stack.name ||
              ""
            ).toLowerCase()
        );

        /*
         * Use the card's real Update button when available so the
         * individual card also shows progress. A detached button is
         * sufficient if the card was re-rendered meanwhile.
         */
        const stackButton =
          card?.querySelector(".docker-update") ||
          document.createElement("button");

        if (!stackButton.textContent) {
          stackButton.textContent = "↑";
        }

        const ok = await redeployStack(
          stack,
          stackButton,
          "update",
          {
            suppressPoll: true
          }
        );

        if (!ok) {
          failures.push(
            stack.display_name ||
            stack.name
          );
        }
      }

      /*
       * Dockhand clears each stack's pending-update state as its
       * pull/redeploy succeeds. One poll at the end updates every
       * arrow and the aggregate Dockhand count together.
       */
      await window.GlanceLive.refresh(
        "docker",
        {
          reason: "update-all-complete"
        }
      );

      if (failures.length) {
        button.textContent =
          `! ${failures.length} failed`;

        button.title =
          `Failed: ${failures.join(", ")}`;
      } else {
        button.textContent = "✓ Updates complete";
        button.title = "All available apps updated";
      }

    } catch (error) {
      console.error(
        "[Docker Live] Update All failed:",
        error
      );

      button.textContent = "!";
      button.title =
        `Update All failed: ${error.message}`;

    } finally {
      window.setTimeout(
        () => {
          button.dataset.busy = "false";
          button.style.opacity = "";
          button.style.pointerEvents = "";

          /*
           * The canonical server refresh may already have replaced
           * this button. Only restore it if it is still connected.
           */
          /*
           * Do not restore the original update count here.
           * The normal Docker poll owns the Dockhand status line
           * and will render the current helper state.
           */
        },
        3000
      );
    }
  }

  /*
   * Delegated because Glance can server-render/replace the Dockhand
   * service-details block at any time.
   */
  document.addEventListener(
    "click",
    event => {
      const button =
        event.target.closest(
          ".docker-update-all"
        );

      if (!button) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      updateAllStacks(button);
    }
  );


  /*
   * FIRST-CLICK UPDATE FALLBACK
   *
   * Handles server-rendered Update buttons immediately,
   * including before the normal Docker poll has run.
   */
  document.addEventListener(
    "click",
    event => {
      const button =
        event.target.closest(
          ".docker-update"
        );

      if (!button) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      const name =
        String(
          button.dataset.updateStack ||
          ""
        ).trim();

      if (
        !name ||
        REDEPLOY_EXCLUDED.has(
          name.toLowerCase()
        )
      ) {
        return;
      }

      redeployStack(
        {
          name
        },
        button,
        "update"
      );
    }
  );

  /*
   * FIRST-CLICK REDEPLOY FALLBACK
   *
   * Glance can insert the server-rendered Docker cards after this
   * script starts. Until the normal Docker poll wires each button,
   * handle clicks here using data-redeploy-stack from docker.yml.
   *
   * Once wireRedeployButton() has run, its existing button listener
   * handles the click and this fallback does nothing.
   */
  document.addEventListener(
    "click",
    event => {
      const button =
        event.target.closest(
          ".docker-redeploy"
        );

      if (
        !button ||
        button.dataset.redeployWired === "true"
      ) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      const name =
        String(
          button.dataset.redeployStack ||
          ""
        ).trim();

      if (
        !name ||
        REDEPLOY_EXCLUDED.has(
          name.toLowerCase()
        )
      ) {
        return;
      }

      redeployStack(
        {
          name
        },
        button
      );
    }
  );

  function wireRedeployButton(
    card,
    stack
  ) {
    const name =
      String(stack?.name || "").trim();

    if (
      !name ||
      REDEPLOY_EXCLUDED.has(
        name.toLowerCase()
      )
    ) {
      return;
    }

    const button =
      card.querySelector(
        ".docker-redeploy"
      );

    if (
      !button ||
      button.dataset.redeployWired
      === "true"
    ) {
      return;
    }

    /*
     * docker.yml owns the button markup and layout.
     * JS only attaches behavior to the server-rendered control.
     */
    button.dataset.redeployWired =
      "true";

    button.dataset.stack = name;

    for (const eventName of [
      "pointerdown",
      "mousedown"
    ]) {
      button.addEventListener(
        eventName,
        event => {
          event.stopPropagation();
        }
      );
    }

    button.addEventListener(
      "click",
      event => {
        event.preventDefault();
        event.stopPropagation();

        redeployStack(
          stack,
          button
        );
      }
    );

    button.addEventListener(
      "mouseenter",
      () => {
        if (
          button.dataset.busy
          !== "true"
        ) {
          button.style.opacity = "1";
        }
      }
    );

    button.addEventListener(
      "mouseleave",
      () => {
        if (
          button.dataset.busy
          !== "true"
        ) {
          button.style.opacity = ".7";
        }
      }
    );
  }


  // ============================================================
  // GENERIC DOCKER CARD STATE
  // ============================================================

  function updateDockhandServiceState(
    card,
    stack
  ) {
    const service =
      stack?.service || {};

    if (
      String(service.type || "").toLowerCase()
      !== "dockhand"
    ) {
      return;
    }

    const updates =
      Number(
        service.updates_available || 0
      );

    let details =
      card.querySelector(
        ":scope > [data-service-details]"
      );

    if (!details) {
      details = document.createElement("div");
      details.className = "size-h6";
      details.setAttribute("data-service-details", "");
      card.appendChild(details);
    }

    let updateAll =
      details.querySelector(
        ".docker-update-all"
      );

    if (updates > 0) {
      if (!updateAll) {
        details.innerHTML = "";

        updateAll =
          document.createElement(
            "button"
          );

        updateAll.type = "button";
        updateAll.className =
          "docker-update-all";

        updateAll.title =
          "Update all available apps";

        updateAll.setAttribute(
          "aria-label",
          "Update all available apps"
        );

        updateAll.style.cssText = `
          appearance:none;
          border:0;
          padding:0;
          margin:0;
          background:none;
          color:#e5c07b;
          font:inherit;
          cursor:pointer;
          text-align:left;
        `;

        details.appendChild(
          updateAll
        );
      }

      updateAll.textContent =
        `${updates} app update${
          updates === 1 ? "" : "s"
        } available`;

      return;
    }

    details.innerHTML = "";

    const current =
      document.createElement("span");

    current.className =
      "color-positive";

    current.textContent =
      "✓ All apps current";

    details.appendChild(current);
  }


  function updateGenericCardState(stack) {
    const name = stack?.name;
    const cardName =
      stack?.display_name || name;

    if (!name) {
      return;
    }

    /*
     * A card may be rendered under its configured display_name rather
     * than its Docker/Compose project name. Match either identity so
     * live health state and update controls reach renamed cards too.
     */
    const card = [...document.querySelectorAll("[data-docker-stack]")]
      .find(
        el => {
          const rendered =
            String(
              el.dataset.dockerStack || ""
            ).toLowerCase();

          return (
            rendered ===
              String(name).toLowerCase()
            ||
            rendered ===
              String(cardName).toLowerCase()
          );
        }
      );

    if (!card) {
      return;
    }

    updateDockhandServiceState(
      card,
      stack
    );

    wireRedeployButton(
      card,
      stack
    );

    const header = card.querySelector(":scope > div > .text-truncate");

    if (!header) {
      return;
    }

    /*
     * Keep card actions pinned to the right edge:
     *
     *   Name                         ↻  ●
     *
     * The title consumes all remaining horizontal space.
     */
    header.style.flex = "1 1 auto";
    header.style.minWidth = "0";

    /*
     * Keep the server-rendered Docker status indicator synchronized
     * with the latest backend state.
     *
     * The indicator is the direct <span> sibling of the header.
     */
    const statusIndicator =
      card.querySelector(
        ".docker-status"
      );

    if (statusIndicator) {
      const color = String(stack.color || "").toLowerCase();
      const running = Number(stack.running || 0);
      const containers = Number(stack.containers || 0);

      if (color === "green") {
        statusIndicator.style.color = "#7fd88f";
        statusIndicator.title = "Running and healthy";
        statusIndicator.textContent = "●";

      } else if (color === "yellow") {
        statusIndicator.style.color = "#e5c07b";
        statusIndicator.style.whiteSpace = "nowrap";
        statusIndicator.title = "Degraded";
        statusIndicator.textContent =
          `● ${running}/${containers}`;

      } else {
        statusIndicator.style.color = "#e06c75";
        statusIndicator.title = "Stopped";
        statusIndicator.textContent = "●";
      }
    }

    const updateAvailable =
      Boolean(stack.update_available);

    const controls =
      card.querySelector(
        ".docker-card-controls"
      );

    let updateButton =
      controls?.querySelector(
        ".docker-update"
      );

    const excluded =
      REDEPLOY_EXCLUDED.has(
        String(name).toLowerCase()
      );

    if (
      updateAvailable &&
      !excluded &&
      controls &&
      !updateButton
    ) {
      updateButton = make(
        "button",
        "↑",
        `
          appearance:none;
          border:0;
          padding:0;
          margin:0;
          background:none;
          color:#7aa2f7;
          font:inherit;
          font-weight:700;
          line-height:1;
          cursor:pointer;
          flex:none;
        `
      );

      updateButton.type = "button";
      updateButton.className =
        "docker-update";

      updateButton.dataset.updateStack =
        name;

      updateButton.title =
        `Update ${name}`;

      updateButton.setAttribute(
        "aria-label",
        `Update ${name}`
      );

      const redeployButton =
        controls.querySelector(
          ".docker-redeploy"
        );

      controls.insertBefore(
        updateButton,
        redeployButton || controls.firstChild
      );
    }

    if (
      (!updateAvailable || excluded) &&
      updateButton
    ) {
      updateButton.remove();
    }

    const displayName =
      card.dataset.dockerStack || name;

    header.title =
      updateAvailable && !excluded
        ? `${displayName} ↑`
        : displayName;
  }

  // ============================================================
  // LIVE REFRESH
  // ============================================================

  async function refreshDocker({ signal }) {
    const response = await fetch(
      helperUrl(),
      {
        cache: "no-store",
        signal
      }
    );

    if (!response.ok) {
      throw new Error(
        `docker-data returned HTTP ${response.status}`
      );
    }

    const data = await response.json();

    if (!Array.isArray(data.stacks)) {
      throw new Error(
        "docker-data response has no stacks array"
      );
    }

    /*
     * Generic Docker state and rich service details share the same
     * authoritative /docker-stacks payload and refresh lifecycle.
     */
    for (const stack of data.stacks) {
      updateGenericCardState(stack);
      updateServiceDetails(stack);
    }
  }

  if (!window.GlanceLive) {
    throw new Error(
      "GlanceLive runtime is not loaded before docker-live.js"
    );
  }

  window.GlanceLive.register({
    id: "docker",
    interval: POLL_MS,
    timeout: LIVE_FETCH_TIMEOUT_MS,

    when: () =>
      Boolean(
        document.querySelector(
          "[data-docker-stack]"
        )
      ),

    refresh: refreshDocker
  });

  console.info(
    `[Docker Live] Registered with GlanceLive — ${POLL_MS / 1000}s while visible`
  );
})();
