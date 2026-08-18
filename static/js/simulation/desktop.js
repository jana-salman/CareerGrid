document.addEventListener("DOMContentLoaded", () => {
    const desktop = document.getElementById("desktop");
    const windows = document.querySelectorAll(".app-window");
    const dockButtons = document.querySelectorAll(".dock-app");
    const quickOpenButtons = document.querySelectorAll("[data-open-app]");
    const workspace = document.getElementById("careergrid-workspace");
    const layoutIdentity = workspace?.dataset.attemptId || workspace?.dataset.workspaceKey;
    const layoutStorageKey = layoutIdentity
        ? `careergrid-window-layout:${layoutIdentity}` : null;
    const minimumVisibleTitleWidth = 180;
    let highestZIndex = 200;

    function updateClock() {
        const now = new Date();
        const clock = document.getElementById("workspace-clock");
        const date = document.getElementById("workspace-date");
        if (clock) clock.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        if (date) date.textContent = now.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
    }

    function focusWindow(windowElement) {
        highestZIndex += 1;
        windowElement.style.zIndex = highestZIndex;
    }

    function updateDockState(appName, open) {
        const button = document.querySelector(`.dock-app[data-app="${appName}"]`);
        if (button) button.classList.toggle("is-open", open);
    }

    function getSavedLayouts() {
        if (!layoutStorageKey) return {};
        try { return JSON.parse(sessionStorage.getItem(layoutStorageKey)) || {}; } catch { return {}; }
    }

    function saveLayouts() {
        if (!layoutStorageKey) return;
        const layouts = {};
        windows.forEach(windowElement => {
            layouts[windowElement.dataset.window] = {
                left: windowElement.offsetLeft, top: windowElement.offsetTop,
                width: windowElement.offsetWidth, height: windowElement.offsetHeight
            };
        });
        try { sessionStorage.setItem(layoutStorageKey, JSON.stringify(layouts)); } catch { /* Optional UI state only. */ }
    }

    function getMinimumSize(windowElement) {
        const styles = getComputedStyle(windowElement);
        const requestedWidth = Number.parseFloat(styles.getPropertyValue("--window-min-width")) || 360;
        const requestedHeight = Number.parseFloat(styles.getPropertyValue("--window-min-height")) || 260;
        return { width: Math.min(requestedWidth, desktop.clientWidth), height: Math.min(requestedHeight, desktop.clientHeight) };
    }

    function clampWindow(windowElement) {
        if (!desktop) return;
        const minimum = getMinimumSize(windowElement);
        let measuredWidth = windowElement.offsetWidth;
        let measuredHeight = windowElement.offsetHeight;

        // Hidden windows have no layout box. Measure them briefly so their CSS
        // defaults remain intact until the user opens the app for the first time.
        if (!measuredWidth || !measuredHeight) {
            const previousDisplay = windowElement.style.display;
            const previousVisibility = windowElement.style.visibility;
            windowElement.style.display = "flex";
            windowElement.style.visibility = "hidden";
            measuredWidth = windowElement.offsetWidth;
            measuredHeight = windowElement.offsetHeight;
            windowElement.style.display = previousDisplay;
            windowElement.style.visibility = previousVisibility;
        }

        const width = Math.min(desktop.clientWidth, Math.max(minimum.width, measuredWidth));
        const height = Math.min(desktop.clientHeight, Math.max(minimum.height, measuredHeight));
        const maxLeft = Math.max(0, desktop.clientWidth - Math.min(width, minimumVisibleTitleWidth));
        const maxTop = Math.max(0, desktop.clientHeight - 52);
        const left = Math.min(maxLeft, Math.max(0, windowElement.offsetLeft));
        const top = Math.min(maxTop, Math.max(0, windowElement.offsetTop));
        Object.assign(windowElement.style, { width: `${width}px`, height: `${height}px`, left: `${left}px`, top: `${top}px` });
    }

    function restoreLayouts() {
        const layouts = getSavedLayouts();
        windows.forEach(windowElement => {
            const layout = layouts[windowElement.dataset.window];
            if (layout && [layout.left, layout.top, layout.width, layout.height].every(Number.isFinite)) {
                Object.assign(windowElement.style, { left: `${layout.left}px`, top: `${layout.top}px`, width: `${layout.width}px`, height: `${layout.height}px` });
            }
            clampWindow(windowElement);
        });
    }

    function openApp(appName) {
        const windowElement = document.querySelector(`[data-window="${appName}"]`);
        if (!windowElement) return;
        clampWindow(windowElement);
        windowElement.setAttribute("aria-hidden", "false");
        updateDockState(appName, true);
        focusWindow(windowElement);
    }

    function hideWindow(windowElement) {
        windowElement.setAttribute("aria-hidden", "true");
        updateDockState(windowElement.dataset.window, false);
        saveLayouts();
    }

    function addResizeHandles(windowElement) {
        ["n", "ne", "e", "se", "s", "sw", "w", "nw"].forEach(direction => {
            const handle = document.createElement("div");
            handle.className = `window-resize-handle window-resize-handle-${direction}`;
            handle.setAttribute("aria-hidden", "true");
            windowElement.append(handle);
            handle.addEventListener("pointerdown", event => {
                event.preventDefault();
                event.stopPropagation();
                const start = { x: event.clientX, y: event.clientY, left: windowElement.offsetLeft, top: windowElement.offsetTop, width: windowElement.offsetWidth, height: windowElement.offsetHeight };
                const minimum = getMinimumSize(windowElement);
                focusWindow(windowElement);
                document.body.classList.add("is-resizing-window");
                handle.setPointerCapture(event.pointerId);
                const resize = moveEvent => {
                    const deltaX = moveEvent.clientX - start.x;
                    const deltaY = moveEvent.clientY - start.y;
                    let left = start.left, top = start.top, width = start.width, height = start.height;
                    if (direction.includes("e")) width = Math.min(desktop.clientWidth - start.left, Math.max(minimum.width, start.width + deltaX));
                    if (direction.includes("s")) height = Math.min(desktop.clientHeight - start.top, Math.max(minimum.height, start.height + deltaY));
                    if (direction.includes("w")) { width = Math.min(start.left + start.width, Math.max(minimum.width, start.width - deltaX)); left = start.left + start.width - width; }
                    if (direction.includes("n")) { height = Math.min(start.top + start.height, Math.max(minimum.height, start.height - deltaY)); top = start.top + start.height - height; }
                    Object.assign(windowElement.style, { left: `${left}px`, top: `${top}px`, width: `${width}px`, height: `${height}px` });
                };
                const finish = () => {
                    document.body.classList.remove("is-resizing-window");
                    handle.removeEventListener("pointermove", resize);
                    clampWindow(windowElement);
                    saveLayouts();
                };
                handle.addEventListener("pointermove", resize);
                handle.addEventListener("pointerup", finish, { once: true });
                handle.addEventListener("pointercancel", finish, { once: true });
            });
        });
    }

    dockButtons.forEach(button => button.addEventListener("click", () => openApp(button.dataset.app)));
    quickOpenButtons.forEach(button => button.addEventListener("click", () => openApp(button.dataset.openApp)));

    windows.forEach(windowElement => {
        windowElement.addEventListener("pointerdown", () => focusWindow(windowElement));
        addResizeHandles(windowElement);
        windowElement.querySelectorAll("[data-window-action]").forEach(control => control.addEventListener("click", event => {
            event.stopPropagation();
            hideWindow(windowElement);
        }));
        const titlebar = windowElement.querySelector(".window-header");
        if (!titlebar) return;
        titlebar.addEventListener("pointerdown", event => {
            if (event.target.closest(".window-controls")) return;
            event.preventDefault();
            const startX = event.clientX, startY = event.clientY;
            const startLeft = windowElement.offsetLeft, startTop = windowElement.offsetTop;
            titlebar.setPointerCapture(event.pointerId);
            focusWindow(windowElement);
            const move = moveEvent => {
                const left = Math.min(Math.max(0, desktop.clientWidth - minimumVisibleTitleWidth), Math.max(0, startLeft + moveEvent.clientX - startX));
                const top = Math.min(Math.max(0, desktop.clientHeight - 52), Math.max(0, startTop + moveEvent.clientY - startY));
                Object.assign(windowElement.style, { left: `${left}px`, top: `${top}px` });
            };
            const finish = () => { titlebar.removeEventListener("pointermove", move); saveLayouts(); };
            titlebar.addEventListener("pointermove", move);
            titlebar.addEventListener("pointerup", finish, { once: true });
            titlebar.addEventListener("pointercancel", finish, { once: true });
        });
    });

    restoreLayouts();
    window.addEventListener("resize", () => { windows.forEach(clampWindow); saveLayouts(); });
    updateClock();
    window.setInterval(updateClock, 30000);
});
