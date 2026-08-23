document.addEventListener("DOMContentLoaded", async () => {
  "use strict";
  const app = document.getElementById("browser-app");
  const page = document.getElementById("browser-page");
  const devtools = document.getElementById("browser-devtools-content");
  const address = document.getElementById("browser-address");
  const addressForm = document.getElementById("browser-address-form");
  const tabStrip = document.getElementById("browser-tab-strip");
  const loading = document.getElementById("browser-loading");
  const viewport = document.getElementById("browser-viewport");
  const devtoolsToggle = document.getElementById("browser-devtools-toggle");
  if (!app || !page || !devtools || !address || !tabStrip) return;

  const escapeHtml = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (character) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#039;",
        })[character],
    );
  const allowedUrls = new Set([
    "careergrid://home",
    "careergrid://product",
    "careergrid://api-status",
    "careergrid://logs",
    "careergrid://documentation",
    "careergrid://snake",
  ]);
  const titles = {
    "careergrid://home": "Home",
    "careergrid://product": "Product Page",
    "careergrid://api-status": "API Status",
    "careergrid://logs": "Logs",
    "careergrid://documentation": "Documentation",
    "careergrid://snake": "Snake",
  };
  const state = {
    tabs: [],
    activeId: null,
    nextId: 1,
    devtoolsTab: "network",
    devtoolsCollapsed: false,
    requestFilter: "all",
    selectedRequest: 0,
    requests: [],
    consoleLines: [],
    scenario: null,
    frontendPatched: false,
  };
  let snakeInstance = null;

  function buildRequests(scenario) {
    const text = [
      scenario.task?.body,
      scenario.task?.summary,
      ...(scenario.resources || []).map((resource) => resource.content),
    ]
      .filter(Boolean)
      .join("\n");
    const found = new Map();
    for (const match of text.matchAll(
      /\b(GET|POST|PUT|PATCH|DELETE)\s+(\/[A-Za-z0-9_./?=&-]*)/gi,
    )) {
      const method = match[1].toUpperCase(),
        endpoint = match[2],
        key = `${method} ${endpoint}`;
      if (found.has(key)) continue;
      const nearby = text.slice(
        Math.max(0, match.index - 180),
        match.index + 600,
      );
      const status = Number(
        nearby.match(/\b([1-5]\d{2})\b/)?.[1] || (method === "GET" ? 200 : 201),
      );
      const error =
        nearby.match(
          /(?:TypeError|ReferenceError|ValueError|ValidationError|Exception|Error)[:\s][^\n]+/i,
        )?.[0] || "";
      found.set(key, {
        method,
        endpoint,
        status,
        type: "fetch",
        duration: `${38 + found.size * 47} ms`,
        time: new Date(Date.now() - found.size * 1300).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
        requestHeaders: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        requestBody: method === "GET" ? null : { source: "simulated-client" },
        responseHeaders: {
          "Content-Type": "application/json",
          "X-CareerGrid-Simulation": "true",
        },
        responseBody: error ? { error } : { ok: true, endpoint },
        timing: {
          queued: "2 ms",
          waiting: `${26 + found.size * 30} ms`,
          download: "10 ms",
        },
        error,
        evidence: nearby.trim(),
      });
    }
    if (!found.size)
      [
        ["POST", "/api/login", 200],
        ["GET", "/api/users/me", 200],
        ["POST", "/api/orders", 500],
        ["GET", "/api/health", 200],
      ].forEach(([method, endpoint, status], index) =>
        found.set(`${method} ${endpoint}`, {
          method,
          endpoint,
          status,
          type: "fetch",
          duration: `${42 + index * 31} ms`,
          time: new Date(Date.now() - index * 1100).toLocaleTimeString(),
          requestHeaders: { Accept: "application/json" },
          requestBody: method === "GET" ? null : { simulated: true },
          responseHeaders: { "Content-Type": "application/json" },
          responseBody:
            status >= 400 ? { error: "Simulated server error" } : { ok: true },
          timing: {
            queued: "2 ms",
            waiting: `${30 + index * 30} ms`,
            download: "8 ms",
          },
          error: status >= 400 ? "Simulated request failed." : "",
          evidence:
            "Fallback simulated API activity; generated resources contained no endpoint trace.",
        }),
      );
    return [...found.values()];
  }
  function buildConsole(scenario) {
    const lines = [];
    (scenario.resources || []).forEach((resource) =>
      String(resource.content || "")
        .split(/\r?\n/)
        .filter((line) =>
          /error|warn|success|info|exception|\b[1-5]\d{2}\b/i.test(line),
        )
        .slice(0, 20)
        .forEach((line) =>
          lines.push({
            level: /error|exception|\b5\d{2}\b/i.test(line)
              ? "error"
              : /warn/i.test(line)
                ? "warning"
                : "info",
            text: `[${resource.name}] ${line}`,
          }),
        ),
    );
    if (!lines.length)
      lines.push(
        {
          level: "info",
          text: "DevTools connected to the CareerGrid simulated API.",
        },
        { level: "success", text: "Public scenario evidence loaded safely." },
      );
    return lines;
  }
  function activeTab() {
    return state.tabs.find((tab) => tab.id === state.activeId);
  }
  function normalizeUrl(value) {
    const raw = String(value || "")
      .trim()
      .toLowerCase();
    return raw.startsWith("careergrid://")
      ? raw
      : `careergrid://${raw || "home"}`;
  }
  function addTab(url = "careergrid://home") {
    const tab = { id: state.nextId++, history: [url], index: 0 };
    state.tabs.push(tab);
    state.activeId = tab.id;
    renderChrome();
    navigate(url, false);
  }
  function closeTab(id) {
    if (state.tabs.length === 1) {
      state.tabs[0].history = ["careergrid://home"];
      state.tabs[0].index = 0;
      navigate("careergrid://home", false);
      return;
    }
    const index = state.tabs.findIndex((tab) => tab.id === id);
    state.tabs.splice(index, 1);
    if (state.activeId === id)
      state.activeId = state.tabs[Math.max(0, index - 1)].id;
    renderChrome();
    renderPage();
  }
  function navigate(url, record = true) {
    const tab = activeTab();
    if (!tab) return;
    const normalized = normalizeUrl(url);
    if (record && tab.history[tab.index] !== normalized) {
      tab.history = tab.history.slice(0, tab.index + 1);
      tab.history.push(normalized);
      tab.index += 1;
    }
    address.value = normalized;
    loading.classList.add("is-loading");
    window.setTimeout(() => {
      loading.classList.remove("is-loading");
      renderChrome();
      renderPage();
    }, 160);
  }
  function renderChrome() {
    tabStrip.replaceChildren();
    state.tabs.forEach((tab) => {
      const url = tab.history[tab.index],
        item = document.createElement("div");
      item.className = `browser-page-tab ${tab.id === state.activeId ? "is-active" : ""}`;
      item.setAttribute("role", "presentation");
      item.innerHTML = `<button type="button" class="browser-tab-select" data-tab-id="${tab.id}" role="tab" aria-selected="${tab.id === state.activeId}"><span>${escapeHtml(titles[url] || "Not found")}</span></button><button type="button" class="browser-tab-close" data-close-tab="${tab.id}" aria-label="Close ${escapeHtml(titles[url] || "tab")}">×</button>`;
      tabStrip.append(item);
    });
    const tab = activeTab();
    if (tab) address.value = tab.history[tab.index];
    app.querySelector('[data-browser-action="back"]').disabled =
      !tab || tab.index === 0;
    app.querySelector('[data-browser-action="forward"]').disabled =
      !tab || tab.index >= tab.history.length - 1;
  }
  function card(url, icon, title, description) {
    return `<button type="button" class="internal-card" data-internal-url="${escapeHtml(url)}"><span>${icon}</span><strong>${escapeHtml(title)}</strong><small>${escapeHtml(description)}</small></button>`;
  }
  function renderHome() {
    const product =
      state.scenario?.scenario_kind === "frontend_workplace"
        ? card(
            "careergrid://product",
            "▣",
            "Product Preview",
            "Reproduce the Buy Now regression",
          )
        : "";
    return `<section class="internal-page internal-home"><div class="internal-hero"><span>CAREERGRID INTERNAL</span><h1>Developer workspace</h1><p>Inspect the simulated services, review task evidence, or take a debug break.</p></div><div class="internal-card-grid">${product}${card("careergrid://api-status", "◉", "API Status", "Health and incident information")}${card("careergrid://documentation", "⌘", "API Documentation", "Endpoints relevant to this task")}${card("careergrid://logs", "≡", "Logs", "Scenario-derived application events")}${card("careergrid://snake", "◇", "Snake Debug Break", "Take a short break while the deployment finishes.")}</div></section>`;
  }
  function renderProduct() {
    return `<section class="product-demo"><div class="viewport-buttons"><button type="button" data-product-viewport="desktop">Desktop</button><button type="button" data-product-viewport="tablet">Tablet</button><button type="button" data-product-viewport="mobile">Mobile</button></div><div data-product-shell><small>Everyday audio</small><h1>Everyday Headphones</h1><p>Comfortable wireless headphones for work and travel.</p><button type="button" id="buy-now-btn" data-buy-now>Buy Now</button><section class="checkout-panel" hidden data-checkout aria-live="polite">Checkout ready</section></div></section>`;
  }
  function renderStatus() {
    const errors = state.requests.filter((item) => item.status >= 400).length,
      average = state.requests.length
        ? Math.round(
            state.requests.reduce(
              (sum, item) => sum + Number.parseInt(item.duration, 10),
              0,
            ) / state.requests.length,
          )
        : 0;
    return `<section class="internal-page"><div class="internal-page-heading"><span>LIVE SIMULATION</span><h1>API status</h1><p>${escapeHtml(state.scenario?.task?.subject || "Generated workplace services")}</p></div><div class="status-grid"><article><small>API health</small><strong class="status-${errors ? "warning" : "good"}">${errors ? "Degraded" : "Operational"}</strong></article><article><small>Database</small><strong class="status-good">Connected</strong></article><article><small>Authentication</small><strong class="status-good">Operational</strong></article><article><small>Average response</small><strong>${average || "—"} ms</strong></article></div><div class="incident-card"><h2>Recent incidents</h2><p>${errors ? `${errors} failing request${errors === 1 ? "" : "s"} detected in the current public scenario evidence.` : "No recent incidents were found in the generated scenario evidence."}</p></div></section>`;
  }
  function renderDocs() {
    const items = state.requests
      .map(
        (item) =>
          `<article class="endpoint-doc"><b class="method-${item.method.toLowerCase()}">${escapeHtml(item.method)}</b><code>${escapeHtml(item.endpoint)}</code><span>${escapeHtml(item.status >= 400 ? "Investigate this scenario endpoint" : "Simulated endpoint")}</span></article>`,
      )
      .join("");
    return `<section class="internal-page"><div class="internal-page-heading"><span>REFERENCE</span><h1>API documentation</h1><p>Endpoints detected in the current generated task and public resources.</p></div><div class="endpoint-list">${items || "<p>No public endpoints were detected.</p>"}</div></section>`;
  }
  function renderLogs() {
    return `<section class="internal-page"><div class="internal-page-heading"><span>OBSERVABILITY</span><h1>Application logs</h1><p>Public evidence from the current simulation scenario.</p></div><div class="internal-logs">${state.consoleLines.map((line) => `<div class="log-${line.level}"><b>${escapeHtml(line.level.toUpperCase())}</b><span>${escapeHtml(line.text)}</span></div>`).join("")}</div></section>`;
  }
  function renderError(url) {
    return `<section class="internal-page internal-error"><strong>404</strong><h1>Internal page not found</h1><p><code>${escapeHtml(url)}</code> is not an available CareerGrid page.</p><button type="button" data-internal-url="careergrid://home">Return home</button></section>`;
  }
  function updateSnakeActivity() {
    snakeInstance?.setActive(
      activeTab()?.history[activeTab().index] === "careergrid://snake" &&
        app.getAttribute("aria-hidden") === "false",
    );
  }
  function syncDevtools() {
    viewport?.classList.toggle(
      "is-devtools-collapsed",
      state.devtoolsCollapsed,
    );
    devtoolsToggle?.setAttribute(
      "aria-expanded",
      String(!state.devtoolsCollapsed),
    );
    if (devtoolsToggle) {
      devtoolsToggle.textContent = state.devtoolsCollapsed ? "⌃" : "⌄";
      devtoolsToggle.title = state.devtoolsCollapsed
        ? "Expand DevTools"
        : "Collapse DevTools";
    }
  }
  function renderPage() {
    snakeInstance?.destroy();
    snakeInstance = null;
    const url = activeTab()?.history[activeTab().index] || "careergrid://home";
    state.devtoolsCollapsed = url === "careergrid://snake";
    if (url === "careergrid://snake") {
      page.replaceChildren();
      snakeInstance = window.CareerGridSnake?.mount(page) || null;
    } else if (!allowedUrls.has(url)) page.innerHTML = renderError(url);
    else
      page.innerHTML =
        url === "careergrid://home"
          ? renderHome()
          : url === "careergrid://product"
            ? renderProduct()
            : url === "careergrid://api-status"
              ? renderStatus()
              : url === "careergrid://documentation"
                ? renderDocs()
                : renderLogs();
    page
      .querySelectorAll("[data-internal-url]")
      .forEach((button) =>
        button.addEventListener("click", () =>
          navigate(button.dataset.internalUrl),
        ),
      );
    page.querySelectorAll("[data-product-viewport]").forEach((button) =>
      button.addEventListener("click", () => {
        const shell = page.querySelector("[data-product-shell]");
        shell.className = button.dataset.productViewport;
      }),
    );
    page.querySelector("[data-buy-now]")?.addEventListener("click", () => {
      if (state.frontendPatched) {
        page.querySelector("[data-checkout]").hidden = false;
        state.consoleLines.push({
          level: "success",
          text: "Checkout panel opened without console errors.",
        });
      } else
        state.consoleLines.push({
          level: "error",
          text: "TypeError: checkoutButton is null; click listener was not registered.",
        });
      renderDevtools();
    });
    renderDevtools();
    syncDevtools();
    updateSnakeActivity();
  }
  function filteredRequests() {
    return state.requests.filter(
      (item) =>
        state.requestFilter === "all" ||
        state.requestFilter === "xhr" ||
        (state.requestFilter === "errors" && item.status >= 400) ||
        (state.requestFilter === "success" && item.status < 400),
    );
  }
  function renderNetwork() {
    const requests = filteredRequests();
    const selected = requests[state.selectedRequest] || requests[0];
    const rows = requests
      .map(
        (item, index) =>
          `<button type="button" class="network-row ${index === state.selectedRequest ? "is-selected" : ""}" data-request-index="${index}"><span>${escapeHtml(item.method)}</span><span>${escapeHtml(item.endpoint)}</span><span class="status-${item.status >= 400 ? "bad" : "good"}">${item.status}</span><span>${escapeHtml(item.type)}</span><span>${escapeHtml(item.duration)}</span><span>${escapeHtml(item.time)}</span></button>`,
      )
      .join("");
    const details = selected
      ? `<div class="network-detail"><h3>${escapeHtml(selected.method)} ${escapeHtml(selected.endpoint)}</h3><dl><dt>Request URL</dt><dd>careergrid://api${escapeHtml(selected.endpoint)}</dd><dt>Method</dt><dd>${escapeHtml(selected.method)}</dd><dt>Status</dt><dd>${selected.status}</dd><dt>Request headers</dt><dd><pre>${escapeHtml(JSON.stringify(selected.requestHeaders, null, 2))}</pre></dd><dt>Request body</dt><dd><pre>${escapeHtml(JSON.stringify(selected.requestBody, null, 2))}</pre></dd><dt>Response headers</dt><dd><pre>${escapeHtml(JSON.stringify(selected.responseHeaders, null, 2))}</pre></dd><dt>Response body</dt><dd><pre>${escapeHtml(JSON.stringify(selected.responseBody, null, 2))}</pre></dd><dt>Timing</dt><dd><pre>${escapeHtml(JSON.stringify(selected.timing, null, 2))}</pre></dd>${selected.error ? `<dt>Error</dt><dd class="status-bad">${escapeHtml(selected.error)}</dd>` : ""}</dl></div>`
      : `<div class="devtools-empty">No requests match this filter.</div>`;
    return `<div class="network-tools">${[
      ["all", "All"],
      ["xhr", "Fetch/XHR"],
      ["errors", "Errors"],
      ["success", "Successful"],
    ]
      .map(
        ([key, label]) =>
          `<button type="button" data-network-filter="${key}" class="${state.requestFilter === key ? "is-active" : ""}">${label}</button>`,
      )
      .join(
        "",
      )}<button type="button" data-clear-network>Clear</button></div><div class="network-table"><div class="network-columns"><span>Method</span><span>Endpoint</span><span>Status</span><span>Type</span><span>Duration</span><span>Time</span></div>${rows}</div>${details}`;
  }
  function renderConsole() {
    return `<div class="console-output" id="console-output">${state.consoleLines.map((line) => `<div class="console-${line.level}"><b>${escapeHtml(line.level)}</b> ${escapeHtml(line.text)}</div>`).join("")}</div><form class="console-command" id="console-command"><span>›</span><input aria-label="Console command" autocomplete="off" placeholder="Type help"><button>Run</button></form>`;
  }
  function renderElements() {
    return `<div class="element-tree">&lt;button <span class="bad">id=&quot;buy-now-btn&quot;</span> type=&quot;button&quot;&gt;Buy Now&lt;/button&gt;<br>&lt;section id=&quot;checkout-panel&quot; hidden&gt;Checkout ready&lt;/section&gt;</div>`;
  }
  function runCommand(command) {
    const value = command.trim().toLowerCase();
    const responses = {
      help: "Commands: help, clear, location, show errors, show requests, open snake",
      location: activeTab()?.history[activeTab().index],
      "show errors": `${state.requests.filter((item) => item.status >= 400).length} request error(s).`,
      "show requests": `${state.requests.length} request(s) recorded.`,
    };
    if (value === "clear") state.consoleLines = [];
    else if (value === "open snake") {
      state.consoleLines.push({
        level: "success",
        text: "Opening careergrid://snake",
      });
      navigate("careergrid://snake");
      return;
    } else
      state.consoleLines.push({
        level: responses[value] ? "success" : "warning",
        text: responses[value] || `Unknown command: ${command}. Type help.`,
      });
    renderDevtools();
  }
  function renderDevtools() {
    devtools.innerHTML =
      state.devtoolsTab === "network"
        ? renderNetwork()
        : state.devtoolsTab === "elements"
          ? renderElements()
          : renderConsole();
    devtools.querySelectorAll("[data-network-filter]").forEach((button) =>
      button.addEventListener("click", () => {
        state.requestFilter = button.dataset.networkFilter;
        state.selectedRequest = 0;
        renderDevtools();
      }),
    );
    devtools.querySelectorAll("[data-request-index]").forEach((button) =>
      button.addEventListener("click", () => {
        state.selectedRequest = Number(button.dataset.requestIndex);
        renderDevtools();
      }),
    );
    devtools
      .querySelector("[data-clear-network]")
      ?.addEventListener("click", () => {
        state.requests = [];
        state.selectedRequest = 0;
        renderDevtools();
      });
    devtools
      .querySelector("#console-command")
      ?.addEventListener("submit", (event) => {
        event.preventDefault();
        const input = event.currentTarget.querySelector("input");
        runCommand(input.value);
      });
  }

  addressForm.addEventListener("submit", (event) => {
    event.preventDefault();
    navigate(address.value);
  });
  app.addEventListener("click", (event) => {
    const action = event.target.closest("[data-browser-action]")?.dataset
        .browserAction,
      tab = activeTab();
    if (action === "new-tab") addTab();
    if (action === "home") navigate("careergrid://home");
    if (action === "reload") renderPage();
    if (action === "back" && tab?.index > 0) {
      tab.index -= 1;
      renderChrome();
      renderPage();
    }
    if (action === "forward" && tab && tab.index < tab.history.length - 1) {
      tab.index += 1;
      renderChrome();
      renderPage();
    }
  });
  tabStrip.addEventListener("click", (event) => {
    const closeId = event.target.closest("[data-close-tab]")?.dataset.closeTab;
    if (closeId) {
      event.stopPropagation();
      closeTab(Number(closeId));
      return;
    }
    const id = event.target.closest("[data-tab-id]")?.dataset.tabId;
    if (id) {
      state.activeId = Number(id);
      renderChrome();
      renderPage();
    }
  });
  document.querySelectorAll("[data-devtools-tab]").forEach((button) =>
    button.addEventListener("click", () => {
      state.devtoolsTab = button.dataset.devtoolsTab;
      document
        .querySelectorAll("[data-devtools-tab]")
        .forEach((item) => item.classList.toggle("is-active", item === button));
      renderDevtools();
    }),
  );
  devtoolsToggle?.addEventListener("click", () => {
    state.devtoolsCollapsed = !state.devtoolsCollapsed;
    syncDevtools();
  });
  new MutationObserver(updateSnakeActivity).observe(app, {
    attributes: true,
    attributeFilter: ["aria-hidden"],
  });
  window.addEventListener("beforeunload", () => snakeInstance?.destroy(), {
    once: true,
  });
  window.CareerGridBrowser = {
    navigate,
    setFrontendPatched(value) {
      state.frontendPatched = Boolean(value);
      renderPage();
    },
  };

  addTab();
  if (!app.dataset.attemptId) {
    state.consoleLines = [
      { level: "warning", text: "No generated workplace attempt is attached." },
    ];
    renderPage();
    return;
  }
  try {
    const response = await fetch(
      `/api/simulation/attempts/${encodeURIComponent(app.dataset.attemptId)}`,
      { credentials: "same-origin" },
    );
    if (!response.ok) throw new Error("Scenario could not be loaded.");
    const payload = await response.json();
    state.scenario = payload.public_scenario || {};
    state.requests = buildRequests(state.scenario);
    state.consoleLines = buildConsole(state.scenario);
    renderPage();
  } catch (error) {
    state.consoleLines = [
      { level: "error", text: "Public scenario evidence could not be loaded." },
    ];
    renderPage();
  }
});
