document.addEventListener("DOMContentLoaded", () => {
    "use strict";
    const windows = [...document.querySelectorAll(".desktop > .app-window")];
    const dockButtons = [...document.querySelectorAll(".dock-app[data-app]")];
    const quickOpenButtons = document.querySelectorAll("[data-open-app]");
    const desktop = document.getElementById("desktop");

    function updateClock() {
        const now = new Date();
        const clock = document.getElementById("workspace-clock");
        const date = document.getElementById("workspace-date");
        if (clock) clock.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        if (date) date.textContent = now.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
    }

    function setActiveApp(appName) {
        let matched = false;
        windows.forEach(windowElement => {
            const active = windowElement.dataset.window === appName;
            matched ||= active;
            windowElement.classList.toggle("is-active", active);
            windowElement.setAttribute("aria-hidden", String(!active));
            windowElement.dispatchEvent(new CustomEvent("careergrid:app-visibility", {
                detail: { active },
            }));
        });
        dockButtons.forEach(button => {
            const active = button.dataset.app === appName && matched;
            button.classList.toggle("is-open", active);
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });
        desktop?.classList.toggle("has-active-app", matched);
    }

    dockButtons.forEach(button => {
        button.setAttribute("aria-pressed", "false");
        button.addEventListener("click", () => setActiveApp(button.dataset.app));
    });
    quickOpenButtons.forEach(button => button.addEventListener("click", () => setActiveApp(button.dataset.openApp)));
    windows.forEach(windowElement => {
        windowElement.classList.remove("is-active");
        windowElement.setAttribute("aria-hidden", "true");
        windowElement.querySelectorAll("[data-window-action]").forEach(control => {
            control.addEventListener("click", event => {
                event.stopPropagation();
                setActiveApp(null);
            });
        });
    });

    updateClock();
    window.setInterval(updateClock, 30000);
});
