document.addEventListener(
    "DOMContentLoaded",
    () => {

        const app =
            document.getElementById(
                "files-app"
            );


        const simulationState =
            window.CareerGridSimulationState;


        if (
            !app
            ||
            !simulationState
        ) {

            return;

        }


        // =========================================
        // ELEMENTS
        // =========================================

        const locationButtons =
            app.querySelectorAll(
                "[data-files-path]"
            );


        const breadcrumb =
            document.getElementById(
                "files-breadcrumb"
            );


        const fileList =
            document.getElementById(
                "files-list"
            );


        const previewEmpty =
            document.getElementById(
                "files-preview-empty"
            );


        const previewContent =
            document.getElementById(
                "files-preview-content"
            );


        const previewIcon =
            document.getElementById(
                "files-preview-icon"
            );


        const previewName =
            document.getElementById(
                "files-preview-name"
            );


        const previewType =
            document.getElementById(
                "files-preview-type"
            );


        const previewActions =
            document.getElementById(
                "files-preview-actions"
            );


        const textPreview =
            document.getElementById(
                "files-text-preview"
            );


        const archivePreview =
            document.getElementById(
                "files-archive-preview"
            );


        const refreshButton =
            document.getElementById(
                "files-refresh-button"
            );


        const toast =
            document.getElementById(
                "files-toast"
            );


        let currentPath =
            "/Downloads";


        let selectedPath =
            null;


        // =========================================
        // HELPERS
        // =========================================

        function escapeHtml(
            value = ""
        ) {

            return String(value)
                .replaceAll(
                    "&",
                    "&amp;"
                )
                .replaceAll(
                    "<",
                    "&lt;"
                )
                .replaceAll(
                    ">",
                    "&gt;"
                )
                .replaceAll(
                    '"',
                    "&quot;"
                )
                .replaceAll(
                    "'",
                    "&#039;"
                );

        }


        function showToast(
            message
        ) {

            toast.textContent =
                message;

            toast.hidden =
                false;


            window.clearTimeout(
                showToast.timeout
            );


            showToast.timeout =
                window.setTimeout(
                    () => {

                        toast.hidden =
                            true;

                    },
                    2300
                );

        }


        function getIcon(
            node
        ) {

            if (
                node.type
                === "folder"
            ) {

                return "▰";

            }


            if (
                node.type
                === "archive"
            ) {

                return "ZIP";

            }


            const type =
                (
                    node.fileType
                    ||
                    ""
                )
                    .toLowerCase();


            if (
                type.includes(
                    "python"
                )
            ) {

                return "PY";

            }


            if (
                type.includes(
                    "log"
                )
            ) {

                return "LOG";

            }


            if (
                type.includes(
                    "markdown"
                )
            ) {

                return "MD";

            }


            return "FILE";

        }


        function typeLabel(
            node
        ) {

            if (
                node.type
                === "folder"
            ) {

                return "Folder";

            }


            if (
                node.type
                === "archive"
            ) {

                return (
                    node.fileType
                    ||
                    "Archive"
                );

            }


            return (
                node.fileType
                ||
                "File"
            );

        }


        // =========================================
        // BREADCRUMB
        // =========================================

        function renderBreadcrumb() {

            breadcrumb.innerHTML =
                "";


            const homeButton =
                document.createElement(
                    "button"
                );


            homeButton.type =
                "button";

            homeButton.className =
                "files-breadcrumb-button";

            homeButton.textContent =
                "Home";


            homeButton.addEventListener(
                "click",
                () => {

                    navigateTo(
                        "/"
                    );

                }
            );


            breadcrumb.appendChild(
                homeButton
            );


            const parts =
                currentPath
                    .split("/")
                    .filter(Boolean);


            let cumulative =
                "";


            parts.forEach(
                part => {

                    cumulative +=
                        `/${part}`;


                    const separator =
                        document.createElement(
                            "span"
                        );


                    separator.className =
                        "files-breadcrumb-separator";

                    separator.textContent =
                        "›";


                    breadcrumb.appendChild(
                        separator
                    );


                    const button =
                        document.createElement(
                            "button"
                        );


                    button.type =
                        "button";

                    button.className =
                        "files-breadcrumb-button";

                    button.textContent =
                        part;


                    const destination =
                        cumulative;


                    button.addEventListener(
                        "click",
                        () => {

                            navigateTo(
                                destination
                            );

                        }
                    );


                    breadcrumb.appendChild(
                        button
                    );

                }
            );

        }


        // =========================================
        // SIDEBAR
        // =========================================

        function updateSidebar() {

            locationButtons.forEach(
                button => {

                    const path =
                        button.dataset
                            .filesPath;


                    button.classList.toggle(
                        "is-active",
                        (
                            path === currentPath
                            ||
                            (
                                path !== "/"
                                &&
                                currentPath.startsWith(
                                    path + "/"
                                )
                            )
                        )
                    );

                }
            );

        }


        // =========================================
        // LIST
        // =========================================

        function renderList() {

            const items =
                simulationState
                    .list(
                        currentPath
                    );


            items.sort(
                (a, b) => {

                    if (
                        a.type === "folder"
                        &&
                        b.type !== "folder"
                    ) {

                        return -1;

                    }


                    if (
                        a.type !== "folder"
                        &&
                        b.type === "folder"
                    ) {

                        return 1;

                    }


                    return a.name
                        .localeCompare(
                            b.name
                        );

                }
            );


            fileList.innerHTML =
                "";


            if (
                items.length
                === 0
            ) {

                fileList.innerHTML =
                    `
                    <div class="files-empty-folder">
                        This folder is empty.
                    </div>
                    `;

                return;

            }


            items.forEach(
                item => {

                    const row =
                        document.createElement(
                            "button"
                        );


                    row.type =
                        "button";


                    row.className =
                        "files-row";


                    if (
                        selectedPath
                        ===
                        item.path
                    ) {

                        row.classList.add(
                            "is-selected"
                        );

                    }


                    const iconClass =
                        item.type
                        === "folder"
                            ?
                            "folder"
                            :
                        item.type
                        === "archive"
                            ?
                            "archive"
                            :
                            "";


                    row.innerHTML =
                        `
                        <span class="files-name-cell">

                            <span
                                class="
                                    files-item-icon
                                    ${iconClass}
                                "
                            >
                                ${escapeHtml(
                                    getIcon(
                                        item
                                    )
                                )}
                            </span>

                            <span class="files-name">
                                ${escapeHtml(
                                    item.name
                                )}
                            </span>

                        </span>


                        <span class="files-type">
                            ${escapeHtml(
                                typeLabel(
                                    item
                                )
                            )}
                        </span>


                        <span class="files-size">
                            ${escapeHtml(
                                item.size
                                ||
                                "—"
                            )}
                        </span>
                        `;


                    row.addEventListener(
                        "click",
                        () => {

                            if (
                                item.type
                                === "folder"
                            ) {

                                navigateTo(
                                    item.path
                                );

                                return;

                            }


                            selectItem(
                                item.path
                            );

                        }
                    );


                    fileList.appendChild(
                        row
                    );

                }
            );

        }


        // =========================================
        // PREVIEW
        // =========================================

        function clearPreview() {

            selectedPath =
                null;


            previewEmpty.hidden =
                false;


            previewContent.hidden =
                true;


            textPreview.hidden =
                true;


            archivePreview.hidden =
                true;


            previewActions.innerHTML =
                "";

        }


        function selectItem(
            path
        ) {

            selectedPath =
                path;


            const node =
                simulationState
                    .read(
                        path
                    );


            if (!node) {

                clearPreview();

                return;

            }


            previewEmpty.hidden =
                true;


            previewContent.hidden =
                false;


            previewIcon.textContent =
                getIcon(
                    node
                );


            previewName.textContent =
                node.name;


            previewType.textContent =
                `${typeLabel(node)} • ${node.size || "Unknown size"}`;


            previewActions.innerHTML =
                "";


            textPreview.hidden =
                true;


            archivePreview.hidden =
                true;


            if (
                node.type
                === "archive"
            ) {

                renderArchivePreview(
                    node,
                    path
                );

            }
            else if (
                node.type
                === "file"
            ) {

                renderTextPreview(
                    node
                );

            }


            renderList();

        }


        function renderTextPreview(
            node
        ) {

            textPreview.hidden =
                false;


            textPreview.textContent =
                node.content
                ||
                "No preview available.";

        }


        function renderArchivePreview(
            node,
            path
        ) {

            archivePreview.hidden =
                false;


            const entries =
                Object.keys(
                    node.archiveEntries
                    ||
                    {}
                );


            archivePreview.innerHTML =
                `
                <div class="files-archive-title">
                    Archive contents
                </div>

                ${
                    entries
                        .map(
                            entry =>
                                `
                                <div class="files-archive-entry">
                                    ${escapeHtml(entry)}
                                </div>
                                `
                        )
                        .join("")
                }
                `;


            const extractButton =
                document.createElement(
                    "button"
                );


            extractButton.type =
                "button";


            extractButton.className =
                "files-action-button";


            extractButton.textContent =
                "Extract to Projects";


            extractButton.addEventListener(
                "click",
                () => {

                    const result =
                        simulationState
                            .extractArchive(
                                path,
                                "/Projects"
                            );


                    if (
                        result.success
                    ) {

                        showToast(
                            "Project extracted to Projects"
                        );


                        navigateTo(
                            result.projectPath
                        );

                    }
                    else {

                        showToast(
                            result.message
                        );

                    }

                }
            );


            previewActions.appendChild(
                extractButton
            );

        }


        // =========================================
        // NAVIGATION
        // =========================================

        function navigateTo(
            path
        ) {

            currentPath =
                path;


            clearPreview();

            updateSidebar();

            renderBreadcrumb();

            renderList();

        }


        // =========================================
        // EVENTS
        // =========================================

        locationButtons.forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        navigateTo(
                            button.dataset
                                .filesPath
                        );

                    }
                );

            }
        );


        refreshButton.addEventListener(
            "click",
            () => {

                renderList();


                if (
                    selectedPath
                ) {

                    selectItem(
                        selectedPath
                    );

                }

            }
        );


        // React immediately if Mail downloads a file.
        window.addEventListener(
            "careergrid:filesystem-changed",
            () => {

                renderList();


                if (
                    selectedPath
                ) {

                    selectItem(
                        selectedPath
                    );

                }

            }
        );


        // =========================================
        // INITIALIZE
        // =========================================

        navigateTo(
            "/Downloads"
        );

    }
);