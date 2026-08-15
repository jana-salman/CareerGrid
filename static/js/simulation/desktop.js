document.addEventListener(
    "DOMContentLoaded",
    () => {

        const windows =
            document.querySelectorAll(
                ".app-window"
            );

        const dockButtons =
            document.querySelectorAll(
                ".dock-app"
            );

        const quickOpenButtons =
            document.querySelectorAll(
                "[data-open-app]"
            );

        let highestZIndex = 200;


        // =========================================
        // CLOCK
        // =========================================

        function updateClock() {

            const now = new Date();

            const clock =
                document.getElementById(
                    "workspace-clock"
                );

            const date =
                document.getElementById(
                    "workspace-date"
                );


            if (clock) {

                clock.textContent =
                    now.toLocaleTimeString(
                        [],
                        {
                            hour: "2-digit",
                            minute: "2-digit"
                        }
                    );

            }


            if (date) {

                date.textContent =
                    now.toLocaleDateString(
                        [],
                        {
                            month: "short",
                            day: "numeric",
                            year: "numeric"
                        }
                    );

            }

        }


        // =========================================
        // WINDOW MANAGEMENT
        // =========================================

        function focusWindow(windowElement) {

            highestZIndex += 1;

            windowElement.style.zIndex =
                highestZIndex;

        }


        function updateDockState(
            appName,
            open
        ) {

            const button =
                document.querySelector(
                    `.dock-app[data-app="${appName}"]`
                );

            if (!button) {
                return;
            }

            button.classList.toggle(
                "is-open",
                open
            );

        }


        function openApp(appName) {

            const windowElement =
                document.querySelector(
                    `[data-window="${appName}"]`
                );

            if (!windowElement) {
                return;
            }


            windowElement.setAttribute(
                "aria-hidden",
                "false"
            );


            updateDockState(
                appName,
                true
            );


            focusWindow(
                windowElement
            );

        }


        function hideWindow(windowElement) {

            const appName =
                windowElement.dataset.window;


            windowElement.setAttribute(
                "aria-hidden",
                "true"
            );


            updateDockState(
                appName,
                false
            );

        }


        // =========================================
        // DOCK
        // =========================================

        dockButtons.forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        openApp(
                            button.dataset.app
                        );

                    }
                );

            }
        );


        quickOpenButtons.forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        openApp(
                            button.dataset.openApp
                        );

                    }
                );

            }
        );


        // =========================================
        // WINDOW CONTROLS
        // =========================================

        windows.forEach(
            windowElement => {

                windowElement.addEventListener(
                    "pointerdown",
                    () => {

                        focusWindow(
                            windowElement
                        );

                    }
                );


                const controls =
                    windowElement.querySelectorAll(
                        "[data-window-action]"
                    );


                controls.forEach(
                    control => {

                        control.addEventListener(
                            "click",
                            event => {

                                event.stopPropagation();

                                hideWindow(
                                    windowElement
                                );

                            }
                        );

                    }
                );


                // =================================
                // DRAG WINDOW
                // =================================

                const titlebar =
                    windowElement.querySelector(
                        ".window-header"
                    );


                if (!titlebar) {
                    return;
                }


                let dragging = false;

                let startX = 0;
                let startY = 0;

                let startLeft = 0;
                let startTop = 0;


                titlebar.addEventListener(
                    "pointerdown",
                    event => {

                        if (
                            event.target.closest(
                                ".window-controls"
                            )
                        ) {
                            return;
                        }


                        dragging = true;

                        startX =
                            event.clientX;

                        startY =
                            event.clientY;

                        startLeft =
                            windowElement.offsetLeft;

                        startTop =
                            windowElement.offsetTop;


                        titlebar.setPointerCapture(
                            event.pointerId
                        );


                        focusWindow(
                            windowElement
                        );

                    }
                );


                titlebar.addEventListener(
                    "pointermove",
                    event => {

                        if (!dragging) {
                            return;
                        }


                        const desktop =
                            document.getElementById(
                                "desktop"
                            );


                        const maxLeft =
                            Math.max(
                                0,
                                desktop.clientWidth - 180
                            );


                        const maxTop =
                            Math.max(
                                0,
                                desktop.clientHeight - 70
                            );


                        const nextLeft =
                            Math.min(
                                maxLeft,
                                Math.max(
                                    0,
                                    startLeft
                                    + event.clientX
                                    - startX
                                )
                            );


                        const nextTop =
                            Math.min(
                                maxTop,
                                Math.max(
                                    0,
                                    startTop
                                    + event.clientY
                                    - startY
                                )
                            );


                        windowElement.style.left =
                            `${nextLeft}px`;


                        windowElement.style.top =
                            `${nextTop}px`;

                    }
                );


                titlebar.addEventListener(
                    "pointerup",
                    () => {

                        dragging = false;

                    }
                );


                titlebar.addEventListener(
                    "pointercancel",
                    () => {

                        dragging = false;

                    }
                );

            }
        );


        // =========================================
        // INITIALIZE
        // =========================================

        updateClock();

        window.setInterval(
            updateClock,
            30000
        );

    }
);