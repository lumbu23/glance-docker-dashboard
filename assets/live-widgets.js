(() => {
  "use strict";

  /*
   * Glance Live Widgets
   *
   * Generic client-side refresh scheduler.
   *
   * This knows nothing about Docker, markets, RSS, weather, Reddit,
   * or any other specific widget. Consumers register a source with:
   *
   *   GlanceLive.register({
   *     id: "docker",
   *     interval: 15000,
   *     when: () => Boolean(document.querySelector("[data-docker-stack]")),
   *     refresh: async ({ signal }) => { ... }
   *   });
   *
   * Responsibilities:
   *   - one timer per source
   *   - no overlapping refreshes
   *   - AbortController lifecycle
   *   - pause while document is hidden
   *   - immediate refresh when document becomes visible
   *   - per-source timeout
   *   - transient/manual refreshes
   *   - source status/introspection
   */

  const sources = new Map();

  const DEFAULT_INTERVAL_MS = 60_000;
  const DEFAULT_TIMEOUT_MS = 15_000;

  function normalizeMs(value, fallback) {
    const number = Number(value);

    return Number.isFinite(number) && number >= 0
      ? number
      : fallback;
  }

  function now() {
    return Date.now();
  }

  function makeState(config) {
    return {
      id: config.id,
      config,

      timer: null,
      transientTimers: new Set(),
      controller: null,

      running: false,
      started: false,
      stopped: false,

      lastAttempt: null,
      lastSuccess: null,
      lastError: null,
      lastDurationMs: null,
      refreshCount: 0,
      errorCount: 0
    };
  }

  function enabled(state) {
    if (state.stopped) {
      return false;
    }

    if (document.hidden) {
      return false;
    }

    const when = state.config.when;

    if (typeof when !== "function") {
      return true;
    }

    try {
      return Boolean(when());
    } catch (error) {
      console.warn(
        `[Glance Live] ${state.id}: when() failed:`,
        error
      );

      return false;
    }
  }

  function clearTimer(state) {
    if (state.timer !== null) {
      window.clearTimeout(state.timer);
      state.timer = null;
    }
  }

  function clearTransientTimers(state) {
    for (const timer of state.transientTimers) {
      window.clearTimeout(timer);
    }

    state.transientTimers.clear();
  }

  function abort(state) {
    if (state.controller) {
      state.controller.abort();
      state.controller = null;
    }
  }

  function intervalFor(state) {
    return normalizeMs(
      state.config.interval,
      DEFAULT_INTERVAL_MS
    );
  }

  function timeoutFor(state) {
    return normalizeMs(
      state.config.timeout,
      DEFAULT_TIMEOUT_MS
    );
  }

  function schedule(state, delay = null) {
    clearTimer(state);

    if (!enabled(state)) {
      return;
    }

    const wait =
      delay === null
        ? intervalFor(state)
        : normalizeMs(delay, intervalFor(state));

    state.timer = window.setTimeout(
      () => {
        state.timer = null;
        refresh(state.id);
      },
      wait
    );
  }

  async function refresh(id, options = {}) {
    const state = sources.get(id);

    if (!state) {
      return false;
    }

    if (!enabled(state) && !options.force) {
      return false;
    }

    if (state.running) {
      return false;
    }

    const refreshFn = state.config.refresh;

    if (typeof refreshFn !== "function") {
      console.warn(
        `[Glance Live] ${id}: no refresh() function`
      );

      return false;
    }

    clearTimer(state);

    state.running = true;
    state.lastAttempt = now();

    const controller = new AbortController();
    state.controller = controller;

    const timeout = window.setTimeout(
      () => controller.abort(),
      timeoutFor(state)
    );

    const startedAt = performance.now();

    try {
      await refreshFn({
        signal: controller.signal,
        id,
        reason: options.reason || "scheduled"
      });

      state.lastSuccess = now();
      state.lastError = null;
      state.refreshCount += 1;

      return true;

    } catch (error) {
      if (error?.name !== "AbortError") {
        state.lastError =
          error instanceof Error
            ? error.message
            : String(error);

        state.errorCount += 1;

        console.warn(
          `[Glance Live] ${id}: refresh failed:`,
          error
        );
      }

      return false;

    } finally {
      window.clearTimeout(timeout);

      state.lastDurationMs =
        Math.round(performance.now() - startedAt);

      if (state.controller === controller) {
        state.controller = null;
      }

      state.running = false;

      if (!options.noReschedule) {
        schedule(state);
      }
    }
  }

  function start(id, options = {}) {
    const state = sources.get(id);

    if (!state || state.stopped) {
      return false;
    }

    if (state.started && !options.force) {
      return true;
    }

    state.started = true;

    if (!enabled(state)) {
      return true;
    }

    if (options.immediate === false) {
      schedule(state);
    } else {
      refresh(id, {
        reason: options.reason || "start"
      });
    }

    return true;
  }

  function stop(id) {
    const state = sources.get(id);

    if (!state) {
      return false;
    }

    state.stopped = true;
    state.started = false;

    clearTimer(state);
    clearTransientTimers(state);
    abort(state);

    return true;
  }

  function resume(id, options = {}) {
    const state = sources.get(id);

    if (!state) {
      return false;
    }

    state.stopped = false;

    return start(id, {
      immediate: options.immediate !== false,
      force: true,
      reason: options.reason || "resume"
    });
  }

  function refreshLater(id, delay, reason = "transient") {
    const state = sources.get(id);

    if (!state) {
      return null;
    }

    const timer = window.setTimeout(
      () => {
        state.transientTimers.delete(timer);

        refresh(id, {
          reason
        });
      },
      normalizeMs(delay, 0)
    );

    state.transientTimers.add(timer);

    return timer;
  }

  function register(config) {
    if (
      !config ||
      typeof config !== "object" ||
      !String(config.id || "").trim()
    ) {
      throw new Error(
        "GlanceLive.register() requires a unique id"
      );
    }

    const id = String(config.id).trim();

    if (sources.has(id)) {
      throw new Error(
        `GlanceLive source already registered: ${id}`
      );
    }

    const normalized = {
      ...config,
      id,
      interval: normalizeMs(
        config.interval,
        DEFAULT_INTERVAL_MS
      ),
      timeout: normalizeMs(
        config.timeout,
        DEFAULT_TIMEOUT_MS
      )
    };

    const state = makeState(normalized);

    sources.set(id, state);

    if (normalized.autoStart !== false) {
      start(id, {
        immediate:
          normalized.immediate !== false,
        reason: "register"
      });
    }

    console.info(
      `[Glance Live] Registered ${id} — ` +
      `${normalized.interval / 1000}s`
    );

    return id;
  }

  function unregister(id) {
    const state = sources.get(id);

    if (!state) {
      return false;
    }

    stop(id);
    sources.delete(id);

    return true;
  }

  function setSourceInterval(
    id,
    interval,
    options = {}
  ) {
    const state = sources.get(id);
    const value = Number(interval);

    if (!state) {
      return false;
    }

    if (
      !Number.isFinite(value) ||
      value < 1
    ) {
      throw new Error(
        `GlanceLive.setInterval(): invalid interval for ${id}`
      );
    }

    state.config.interval = value;

    /*
     * A refresh normally calls this while running. Its finally block
     * will schedule using the newly learned interval. Allow callers
     * outside a refresh to request an immediate reschedule as well.
     */
    if (
      options.reschedule !== false &&
      state.started &&
      !state.stopped &&
      !state.running &&
      !document.hidden
    ) {
      schedule(state);
    }

    return true;
  }

  function status(id = null) {
    const serialize = state => ({
      id: state.id,
      running: state.running,
      started: state.started,
      stopped: state.stopped,
      interval: intervalFor(state),
      timeout: timeoutFor(state),
      lastAttempt: state.lastAttempt,
      lastSuccess: state.lastSuccess,
      lastError: state.lastError,
      lastDurationMs: state.lastDurationMs,
      refreshCount: state.refreshCount,
      errorCount: state.errorCount
    });

    if (id !== null) {
      const state = sources.get(id);

      return state
        ? serialize(state)
        : null;
    }

    return Object.fromEntries(
      [...sources.entries()].map(
        ([sourceId, state]) => [
          sourceId,
          serialize(state)
        ]
      )
    );
  }

  function handleVisibility() {
    if (document.hidden) {
      for (const state of sources.values()) {
        clearTimer(state);
        clearTransientTimers(state);
        abort(state);
      }

      return;
    }

    for (const state of sources.values()) {
      if (
        state.started &&
        !state.stopped &&
        enabled(state)
      ) {
        refresh(state.id, {
          reason: "visible"
        });
      }
    }
  }

  document.addEventListener(
    "visibilitychange",
    handleVisibility
  );

  /*
   * A source can register before Glance has finished rendering the
   * DOM elements its when() predicate depends on. Re-evaluate dormant
   * sources when the document changes so individual consumers do not
   * need their own MutationObserver/startup lifecycle.
   */
  let domCheckQueued = false;

  function checkDormantSources() {
    domCheckQueued = false;

    if (document.hidden) {
      return;
    }

    for (const state of sources.values()) {
      if (
        state.started &&
        !state.stopped &&
        !state.running &&
        state.timer === null &&
        enabled(state)
      ) {
        refresh(state.id, {
          reason: "dom-ready"
        });
      }
    }
  }

  const domObserver = new MutationObserver(() => {
    if (domCheckQueued) {
      return;
    }

    domCheckQueued = true;

    window.requestAnimationFrame(
      checkDormantSources
    );
  });

  domObserver.observe(
    document.documentElement,
    {
      childList: true,
      subtree: true
    }
  );

  window.GlanceLive = Object.freeze({
    register,
    unregister,
    start,
    stop,
    resume,
    refresh,
    refreshLater,
    setInterval: setSourceInterval,
    status
  });

  console.info(
    "[Glance Live] Runtime loaded"
  );
})();
