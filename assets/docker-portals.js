(() => {
  /*
   * ------------------------------------------------------------
   * Docker portal links
   * ------------------------------------------------------------
   */

  function buildPortalUrl(link) {
    const port = link.dataset.portalPort || "";
    const path = link.dataset.portalPath || "/";
    const scheme = link.dataset.portalScheme || "";

    if (!port) {
      return null;
    }

    /*
     * Start with the exact URL used to access Glance.
     *
     * Examples:
     *   http://nas.local:30080/home
     *   http://192.168.1.10:30080/home
     *   https://nas.example.ts.net:30080/home
     *
     * hostname/IP is preserved automatically.
     */
    const url = new URL(window.location.href);

    if (scheme) {
      url.protocol = `${scheme}:`;
    }

    url.port = port;
    url.pathname = path;
    url.search = "";
    url.hash = "";

    return url.toString();
  }


  function updatePortalLink(link) {
    const url = buildPortalUrl(link);

    if (!url) {
      return;
    }

    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }


  function updateAllPortalLinks(root = document) {
    if (
      root.nodeType === Node.ELEMENT_NODE &&
      root.matches?.(".docker-portal-link")
    ) {
      updatePortalLink(root);
    }

    if (root.querySelectorAll) {
      root
        .querySelectorAll(".docker-portal-link")
        .forEach(updatePortalLink);
    }
  }


  /*
   * ------------------------------------------------------------
   * Whole-widget links
   * ------------------------------------------------------------
   */

  function buildTrueNasUrl() {
    /*
     * Preserve whatever hostname/IP and protocol were used to
     * access Glance, but remove the Glance port entirely.
     *
     * Examples:
     *
     * http://nas.local:30080/home
     *   -> http://nas.local/
     *
     * http://192.168.1.10:30080/home
     *   -> http://192.168.1.10/
     *
     * https://nas.example.ts.net:30080/home
     *   -> https://nas.example.ts.net/
     */
    const url = new URL(window.location.href);

    url.port = "";
    url.pathname = "/";
    url.search = "";
    url.hash = "";

    return url.toString();
  }


  const WEATHER_URL =
    "https://www.accuweather.com/en/us/ann-arbor/48104/weather-forecast/329380";


  function makeWidgetClickable(widget, url) {
    if (!widget || widget.dataset.wholeWidgetLinkReady === "true") {
      return;
    }

    widget.dataset.wholeWidgetLinkReady = "true";

    widget.style.cursor = "pointer";

    widget.setAttribute("role", "link");
    widget.setAttribute("tabindex", "0");


    function openLink(event) {
      /*
       * If we ever add a real link/button inside one of these widgets,
       * allow that element to behave normally instead.
       */
      if (
        event.target.closest(
          "a, button, input, select, textarea, [role='button']"
        )
      ) {
        return;
      }

      window.open(
        url,
        "_blank",
        "noopener,noreferrer"
      );
    }


    widget.addEventListener(
      "click",
      openLink
    );


    widget.addEventListener(
      "keydown",
      (event) => {
        if (
          event.key === "Enter" ||
          event.key === " "
        ) {
          event.preventDefault();

          window.open(
            url,
            "_blank",
            "noopener,noreferrer"
          );
        }
      }
    );
  }


  function updateWholeWidgetLinks(root = document) {
    /*
     * TrueNAS
     */
    const trueNasUrl = buildTrueNasUrl();

    if (
      root.nodeType === Node.ELEMENT_NODE &&
      root.matches?.(".truenas-home-link")
    ) {
      makeWidgetClickable(
        root,
        trueNasUrl
      );
    }

    if (root.querySelectorAll) {
      root
        .querySelectorAll(".truenas-home-link")
        .forEach(
          (widget) =>
            makeWidgetClickable(
              widget,
              trueNasUrl
            )
        );
    }


    /*
     * Weather
     */
    if (
      root.nodeType === Node.ELEMENT_NODE &&
      root.matches?.(".weather-forecast-link")
    ) {
      makeWidgetClickable(
        root,
        WEATHER_URL
      );
    }

    if (root.querySelectorAll) {
      root
        .querySelectorAll(".weather-forecast-link")
        .forEach(
          (widget) =>
            makeWidgetClickable(
              widget,
              WEATHER_URL
            )
        );
    }
  }


  /*
   * ------------------------------------------------------------
   * Initialization / Glance re-render handling
   * ------------------------------------------------------------
   */

  function updateEverything(root = document) {
    updateAllPortalLinks(root);
    updateWholeWidgetLinks(root);
  }


  function initialize() {
    updateEverything(document);

    /*
     * Glance widgets can be refreshed/re-rendered dynamically,
     * particularly custom-api widgets.
     *
     * Reapply both Docker and whole-widget links whenever new
     * elements appear.
     */
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
          if (
            node.nodeType === Node.ELEMENT_NODE
          ) {
            updateEverything(node);
          }
        }
      }
    });

    observer.observe(
      document.documentElement,
      {
        childList: true,
        subtree: true
      }
    );
  }


  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initialize,
      { once: true }
    );
  } else {
    initialize();
  }
})();
