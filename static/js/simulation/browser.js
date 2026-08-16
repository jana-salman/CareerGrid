document.addEventListener("DOMContentLoaded", async () => {
    const app = document.getElementById("browser-app");
    const content = document.getElementById("browser-content");
    if (!app || !content) return;

    const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[character]);
    const attemptId = app.dataset.attemptId;
    let activeTab = "network";
    let selectedRequest = 0;
    let model = { requests: [], consoleLines: [], task: null };

    function requestEvidence(scenario) {
        const sources = [scenario.task?.body, scenario.task?.summary, ...(scenario.resources || []).map(resource => resource.content)].filter(Boolean);
        const requests = [];
        const byEndpoint = new Map();
        sources.forEach(source => {
            const text = String(source);
            const endpoints = text.matchAll(/\b(GET|POST|PUT|PATCH|DELETE)\s+(\/[A-Za-z0-9_./?=&-]*)/gi);
            for (const match of endpoints) {
                const key = `${match[1].toUpperCase()} ${match[2]}`;
                const nearby = text.slice(Math.max(0, match.index - 220), match.index + 520);
                const statusMatch = nearby.match(/\b([1-5]\d{2})\b/);
                const errorMatch = nearby.match(/(?:TypeError|ReferenceError|ValueError|ValidationError|Exception|Error)[:\s][^\n]+/i);
                const existing = byEndpoint.get(key);
                if (existing) {
                    if (!existing.status && statusMatch) existing.status = Number(statusMatch[1]);
                    if (existing.error === "No response body was provided." && errorMatch) existing.error = errorMatch[0];
                    if (nearby.length > existing.evidence.length) existing.evidence = nearby.trim();
                    continue;
                }
                const request = { method: match[1].toUpperCase(), path: match[2], status: Number(statusMatch?.[1] || 0), type: "fetch", duration: "—", error: errorMatch?.[0] || "No response body was provided.", evidence: nearby.trim() };
                byEndpoint.set(key, request);
                requests.push(request);
            }
        });
        return requests;
    }

    function consoleEvidence(scenario) {
        const lines = [];
        (scenario.resources || []).forEach(resource => {
            const resourceLines = String(resource.content || "").split(/\r?\n/).filter(Boolean);
            resourceLines.forEach(line => {
                if (/error|exception|typeerror|referenceerror|\b[1-5]\d{2}\b|\b(GET|POST|PUT|PATCH|DELETE)\b/i.test(line)) lines.push(`[${resource.name}] ${line}`);
            });
            if (!resourceLines.some(line => /error|exception|typeerror|referenceerror|\b[1-5]\d{2}\b/i.test(line))) lines.push(...resourceLines.slice(0, 12).map(line => `[${resource.name}] ${line}`));
        });
        return lines.slice(0, 80);
    }

    function renderNetwork() {
        if (!model.requests.length) return '<div class="browser-empty-state">No public HTTP/request evidence is available for this scenario.</div>';
        const request = model.requests[selectedRequest] || model.requests[0];
        const statusClass = request.status >= 400 ? "browser-status-error" : "browser-status-ok";
        return `<div class="browser-network"><div class="browser-request-list">${model.requests.map((item, index) => `<button class="browser-request-row ${index === selectedRequest ? "is-selected" : ""}" data-browser-request="${index}"><span class="browser-method">${escapeHtml(item.method)}</span><span>${escapeHtml(item.path)}</span><span class="${item.status >= 400 ? "browser-status-error" : "browser-status-ok"}">${item.status || "—"}</span></button>`).join("")}</div><div class="browser-detail"><h3>${escapeHtml(request.method)} ${escapeHtml(request.path)}</h3><dl><dt>Status</dt><dd class="${statusClass}">${request.status ? `${request.status} ${request.status >= 400 ? "Error" : "OK"}` : "Not provided"}</dd><dt>Type</dt><dd>${escapeHtml(request.type)}</dd><dt>Duration</dt><dd>${escapeHtml(request.duration)}</dd><dt>Evidence</dt><dd>Derived from public task/resources</dd></dl><pre class="browser-code">${escapeHtml(request.error)}\n\n${escapeHtml(request.evidence)}</pre></div></div>`;
    }

    function renderConsole() {
        if (!model.consoleLines.length) return '<div class="browser-empty-state">No public console or log evidence is available for this scenario.</div>';
        return `<div class="browser-console">${model.consoleLines.map(line => `<div class="${/error|exception|typeerror|referenceerror/i.test(line) ? "is-error" : ""}">${escapeHtml(line)}</div>`).join("")}</div>`;
    }

    function renderRequest() {
        const task = model.task;
        if (!task) return '<div class="browser-empty-state">No generated task is available.</div>';
        const request = model.requests[selectedRequest];
        return `<div class="browser-detail"><h3>Task request preview</h3><dl><dt>Task</dt><dd>${escapeHtml(task.subject || task.id)}</dd><dt>Method</dt><dd>${escapeHtml(request?.method || "Not provided")}</dd><dt>Path</dt><dd>${escapeHtml(request?.path || "No public endpoint was found")}</dd><dt>Priority</dt><dd>${escapeHtml(task.priority || "normal")}</dd></dl><pre class="browser-code">${escapeHtml(task.body || task.summary || "")}</pre></div>`;
    }

    function render() {
        content.innerHTML = activeTab === "network" ? renderNetwork() : activeTab === "console" ? renderConsole() : renderRequest();
        content.querySelectorAll("[data-browser-request]").forEach(button => button.addEventListener("click", () => { selectedRequest = Number(button.dataset.browserRequest); render(); }));
    }

    document.querySelectorAll("[data-browser-tab]").forEach(button => button.addEventListener("click", () => { activeTab = button.dataset.browserTab; document.querySelectorAll("[data-browser-tab]").forEach(tab => tab.classList.toggle("is-active", tab === button)); render(); }));
    if (!attemptId) { content.innerHTML = '<div class="browser-empty-state">Browser debugging evidence is available for generated workplace attempts.</div>'; return; }
    try {
        const response = await fetch(`/api/simulation/attempts/${encodeURIComponent(attemptId)}`, { credentials: "same-origin" });
        if (!response.ok) throw new Error("Scenario could not be loaded.");
        const payload = await response.json();
        const scenario = payload.public_scenario;
        if (!scenario) throw new Error("Public scenario is unavailable.");
        model = { task: scenario.task || {}, requests: requestEvidence(scenario), consoleLines: consoleEvidence(scenario) };
        render();
    } catch (error) {
        content.innerHTML = '<div class="browser-empty-state">Browser evidence could not be loaded for this attempt.</div>';
    }
});
