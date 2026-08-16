document.addEventListener(
    "DOMContentLoaded",
    () => {

        const app =
            document.getElementById(
                "vscode-app"
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

        const projectPicker =
            document.getElementById(
                "vscode-project-picker"
            );


        const projectList =
            document.getElementById(
                "vscode-project-list"
            );


        const projectExplorer =
            document.getElementById(
                "vscode-project-explorer"
            );


        const projectName =
            document.getElementById(
                "vscode-project-name"
            );


        const fileTree =
            document.getElementById(
                "vscode-file-tree"
            );


        const closeProjectButton =
            document.getElementById(
                "vscode-close-project"
            );


        const refreshProjectButton =
            document.getElementById(
                "vscode-refresh-project"
            );


        const tabsElement =
            document.getElementById(
                "vscode-tabs"
            );


        const emptyEditor =
            document.getElementById(
                "vscode-empty-editor"
            );


        const editorSection =
            document.getElementById(
                "vscode-editor"
            );


        const codeEditor =
            document.getElementById(
                "vscode-code-editor"
            );


        const lineNumbers =
            document.getElementById(
                "vscode-line-numbers"
            );


        const saveButton =
            document.getElementById(
                "vscode-save-button"
            );


        const breadcrumb =
            document.getElementById(
                "vscode-breadcrumb"
            );


        const statusProject =
            document.getElementById(
                "vscode-status-project"
            );


        const statusPosition =
            document.getElementById(
                "vscode-status-position"
            );


        const statusLanguage =
            document.getElementById(
                "vscode-status-language"
            );


        const searchButton =
            document.getElementById(
                "vscode-search-button"
            );


        const searchPanel =
            document.getElementById(
                "vscode-search-panel"
            );


        const searchInput =
            document.getElementById(
                "vscode-search-input"
            );


        const searchResults =
            document.getElementById(
                "vscode-search-results"
            );


        const closeSearch =
            document.getElementById(
                "vscode-close-search"
            );


        const toast =
            document.getElementById(
                "vscode-toast"
            );


        // =========================================
        // EDITOR STATE
        // =========================================

        let currentProjectPath =
            null;


        let activeFilePath =
            null;


        const openTabs =
            [];


        const editorBuffers =
            new Map();


        const expandedFolders =
            new Set();


        // =========================================
        // HELPERS
        // =========================================

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
                    2200
                );

        }


        function basename(
            path
        ) {

            return path
                .split("/")
                .filter(Boolean)
                .pop()
                ||
                "";

        }


        function relativePath(
            path
        ) {

            if (
                !currentProjectPath
            ) {

                return path;

            }


            return path
                .replace(
                    `${currentProjectPath}/`,
                    ""
                );

        }


        function languageForFile(
            path
        ) {

            const extension =
                path
                    .split(".")
                    .pop()
                    .toLowerCase();


            const languages = {

                py:
                    "Python",

                js:
                    "JavaScript",

                jsx:
                    "JavaScript React",

                ts:
                    "TypeScript",

                tsx:
                    "TypeScript React",

                html:
                    "HTML",

                css:
                    "CSS",

                json:
                    "JSON",

                md:
                    "Markdown",

                txt:
                    "Plain Text",

                log:
                    "Log",

                java:
                    "Java",

                cpp:
                    "C++",

                c:
                    "C",

                cs:
                    "C#",

                sql:
                    "SQL"

            };


            return (
                languages[
                    extension
                ]
                ||
                "Plain Text"
            );

        }


        function iconClassForFile(
            path
        ) {

            const extension =
                path
                    .split(".")
                    .pop()
                    .toLowerCase();


            if (
                extension === "py"
            ) {

                return "python";

            }


            if (
                extension === "md"
            ) {

                return "markdown";

            }


            if (
                extension === "json"
            ) {

                return "json";

            }


            if (
                extension === "js"
                ||
                extension === "ts"
            ) {

                return "javascript";

            }


            if (
                extension === "css"
            ) {

                return "css";

            }


            if (
                extension === "html"
            ) {

                return "html";

            }


            return "";

        }


        function iconLabelForFile(
            path
        ) {

            const extension =
                path
                    .split(".")
                    .pop()
                    .toLowerCase();


            const labels = {

                py:
                    "PY",

                js:
                    "JS",

                jsx:
                    "JS",

                ts:
                    "TS",

                tsx:
                    "TS",

                html:
                    "<>",

                css:
                    "#",

                json:
                    "{}",

                md:
                    "M",

                log:
                    "L",

                txt:
                    "T",

                java:
                    "J",

                cpp:
                    "C++",

                c:
                    "C",

                cs:
                    "C#",

                sql:
                    "SQL"

            };


            return (
                labels[
                    extension
                ]
                ||
                "•"
            );

        }


        // =========================================
        // PROJECT LIST
        // =========================================

        function renderProjectPicker() {

            const projects =
                simulationState
                    .list(
                        "/Projects"
                    )
                    .filter(
                        item =>
                            item.type
                            ===
                            "folder"
                    );


            projectList.innerHTML =
                "";


            if (
                projects.length
                ===
                0
            ) {

                projectList.innerHTML =
                    `
                    <div class="vscode-no-projects">
                        No projects are available yet.

                        Download and extract a project
                        from Files first.
                    </div>
                    `;

                return;

            }


            projects.forEach(
                project => {

                    const button =
                        document.createElement(
                            "button"
                        );


                    button.type =
                        "button";


                    button.className =
                        "vscode-project-option";


                    button.innerHTML =
                        `
                        <span class="vscode-project-folder-icon">
                            ▰
                        </span>

                        <span>
                            ${project.name}
                        </span>
                        `;


                    button.addEventListener(
                        "click",
                        () => {

                            openProject(
                                project.path
                            );

                        }
                    );


                    projectList.appendChild(
                        button
                    );

                }
            );

        }


        function openProject(
            path
        ) {

            const project =
                simulationState
                    .read(
                        path
                    );


            if (
                !project
                ||
                project.type
                !==
                "folder"
            ) {

                showToast(
                    "Unable to open this project."
                );

                return;

            }


            currentProjectPath =
                path;


            expandedFolders.clear();

            expandedFolders.add(
                path
            );


            projectPicker.hidden =
                true;


            projectExplorer.hidden =
                false;


            projectName.textContent =
                basename(
                    path
                );


            statusProject.textContent =
                basename(
                    path
                );


            renderFileTree();

        }


        function closeProject() {

            if (
                hasUnsavedFiles()
            ) {

                const confirmed =
                    window.confirm(
                        "You have unsaved changes. Close the project anyway?"
                    );


                if (!confirmed) {

                    return;

                }

            }


            currentProjectPath =
                null;

            activeFilePath =
                null;


            openTabs.splice(
                0,
                openTabs.length
            );


            editorBuffers.clear();

            expandedFolders.clear();


            projectPicker.hidden =
                false;

            projectExplorer.hidden =
                true;


            statusProject.textContent =
                "No project";


            renderTabs();

            renderEditor();

            renderProjectPicker();

        }


        // =========================================
        // FILE TREE
        // =========================================

        function renderFileTree() {

            fileTree.innerHTML =
                "";


            if (
                !currentProjectPath
            ) {

                return;

            }


            renderFolderChildren(
                currentProjectPath,
                fileTree,
                0
            );

        }


        function renderFolderChildren(
            folderPath,
            container,
            depth
        ) {

            const children =
                simulationState
                    .list(
                        folderPath
                    );


            children.sort(
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


            children.forEach(
                child => {

                    const row =
                        document.createElement(
                            "button"
                        );


                    row.type =
                        "button";


                    row.className =
                        "vscode-tree-row";


                    row.style.paddingLeft =
                        `${8 + (depth * 14)}px`;


                    if (
                        child.path
                        ===
                        activeFilePath
                    ) {

                        row.classList.add(
                            "is-active"
                        );

                    }


                    if (
                        child.type
                        ===
                        "folder"
                    ) {

                        const expanded =
                            expandedFolders
                                .has(
                                    child.path
                                );


                        row.innerHTML =
                            `
                            <span class="vscode-tree-arrow">
                                ${
                                    expanded
                                        ? "⌄"
                                        : "›"
                                }
                            </span>

                            <span class="vscode-tree-icon folder">
                                ▰
                            </span>

                            <span class="vscode-tree-label">
                                ${child.name}
                            </span>
                            `;


                        row.addEventListener(
                            "click",
                            () => {

                                if (
                                    expandedFolders
                                        .has(
                                            child.path
                                        )
                                ) {

                                    expandedFolders
                                        .delete(
                                            child.path
                                        );

                                }
                                else {

                                    expandedFolders
                                        .add(
                                            child.path
                                        );

                                }


                                renderFileTree();

                            }
                        );


                        container.appendChild(
                            row
                        );


                        if (
                            expanded
                        ) {

                            renderFolderChildren(
                                child.path,
                                container,
                                depth + 1
                            );

                        }


                        return;

                    }


                    const iconClass =
                        iconClassForFile(
                            child.path
                        );


                    row.innerHTML =
                        `
                        <span class="vscode-tree-arrow">
                        </span>

                        <span
                            class="
                                vscode-tree-icon
                                ${iconClass}
                            "
                        >
                            ${
                                iconLabelForFile(
                                    child.path
                                )
                            }
                        </span>

                        <span class="vscode-tree-label">
                            ${child.name}
                        </span>
                        `;


                    row.addEventListener(
                        "click",
                        () => {

                            openFile(
                                child.path
                            );

                        }
                    );


                    container.appendChild(
                        row
                    );

                }
            );

        }


        // =========================================
        // OPEN FILES
        // =========================================

        function openFile(
            path
        ) {

            const node =
                simulationState
                    .read(
                        path
                    );


            if (
                !node
                ||
                node.type
                !==
                "file"
            ) {

                return;

            }


            if (
                !editorBuffers
                    .has(
                        path
                    )
            ) {

                editorBuffers.set(
                    path,
                    {
                        original:
                            node.content
                            ||
                            "",

                        current:
                            node.content
                            ||
                            "",

                        dirty:
                            false
                    }
                );

            }


            if (
                !openTabs
                    .includes(
                        path
                    )
            ) {

                openTabs.push(
                    path
                );

            }


            activeFilePath =
                path;


            renderTabs();

            renderFileTree();

            renderEditor();

        }


        function closeTab(
            path
        ) {

            const buffer =
                editorBuffers.get(
                    path
                );


            if (
                buffer?.dirty
            ) {

                const confirmed =
                    window.confirm(
                        `Save changes to ${basename(path)} before closing?`
                    );


                if (
                    confirmed
                ) {

                    saveFile(
                        path
                    );

                }

            }


            const index =
                openTabs.indexOf(
                    path
                );


            if (
                index !== -1
            ) {

                openTabs.splice(
                    index,
                    1
                );

            }


            editorBuffers.delete(
                path
            );


            if (
                activeFilePath
                ===
                path
            ) {

                activeFilePath =
                    openTabs[
                        openTabs.length - 1
                    ]
                    ||
                    null;

            }


            renderTabs();

            renderFileTree();

            renderEditor();

        }


        // =========================================
        // TABS
        // =========================================

        function renderTabs() {

            tabsElement.innerHTML =
                "";


            openTabs.forEach(
                path => {

                    const buffer =
                        editorBuffers.get(
                            path
                        );


                    const tab =
                        document.createElement(
                            "button"
                        );


                    tab.type =
                        "button";


                    tab.className =
                        "vscode-tab";


                    if (
                        path
                        ===
                        activeFilePath
                    ) {

                        tab.classList.add(
                            "is-active"
                        );

                    }


                    tab.innerHTML =
                        `
                        <span class="vscode-tree-icon ${iconClassForFile(path)}">
                            ${iconLabelForFile(path)}
                        </span>

                        <span class="vscode-tab-label">
                            ${basename(path)}
                        </span>

                        ${
                            buffer?.dirty
                                ?
                                `
                                <span class="vscode-tab-unsaved"></span>
                                `
                                :
                                ""
                        }

                        <span
                            class="vscode-tab-close"
                            title="Close"
                        >
                            ×
                        </span>
                        `;


                    tab.addEventListener(
                        "click",
                        event => {

                            if (
                                event.target.closest(
                                    ".vscode-tab-close"
                                )
                            ) {

                                event.stopPropagation();

                                closeTab(
                                    path
                                );

                                return;

                            }


                            activeFilePath =
                                path;


                            renderTabs();

                            renderFileTree();

                            renderEditor();

                        }
                    );


                    tabsElement.appendChild(
                        tab
                    );

                }
            );

        }


        // =========================================
        // EDITOR
        // =========================================

        function renderEditor() {

            if (
                !activeFilePath
            ) {

                emptyEditor.hidden =
                    false;

                editorSection.hidden =
                    true;


                statusLanguage.textContent =
                    "Plain Text";


                statusPosition.textContent =
                    "Ln 1, Col 1";


                return;

            }


            const buffer =
                editorBuffers.get(
                    activeFilePath
                );


            if (!buffer) {

                return;

            }


            emptyEditor.hidden =
                true;

            editorSection.hidden =
                false;


            codeEditor.value =
                buffer.current;


            breadcrumb.textContent =
                relativePath(
                    activeFilePath
                )
                    .replaceAll(
                        "/",
                        "  ›  "
                    );


            statusLanguage.textContent =
                languageForFile(
                    activeFilePath
                );


            saveButton.disabled =
                !buffer.dirty;


            renderLineNumbers();

            updateCursorPosition();

        }


        function renderLineNumbers() {

            const lines =
                codeEditor.value
                    .split("\n")
                    .length;


            lineNumbers.innerHTML =
                "";


            for (
                let index = 1;
                index <= lines;
                index += 1
            ) {

                const number =
                    document.createElement(
                        "div"
                    );


                number.className =
                    "vscode-line-number";


                number.textContent =
                    index;


                lineNumbers.appendChild(
                    number
                );

            }

        }


        function updateEditorBuffer() {

            if (
                !activeFilePath
            ) {

                return;

            }


            const buffer =
                editorBuffers.get(
                    activeFilePath
                );


            if (!buffer) {

                return;

            }


            buffer.current =
                codeEditor.value;


            buffer.dirty =
                (
                    buffer.current
                    !==
                    buffer.original
                );


            saveButton.disabled =
                !buffer.dirty;


            renderTabs();

            renderLineNumbers();

            updateCursorPosition();

        }


        function saveFile(
            path = activeFilePath
        ) {

            if (!path) {

                return;

            }


            const buffer =
                editorBuffers.get(
                    path
                );


            if (!buffer) {

                return;

            }


            const currentNode =
                simulationState
                    .read(
                        path
                    );


            if (!currentNode) {

                showToast(
                    "The file no longer exists."
                );

                return;

            }


            simulationState
                .writeNode(
                    path,
                    {
                        ...currentNode,

                        content:
                            buffer.current,

                        modifiedAt:
                            new Date()
                                .toISOString()
                    }
                );


            buffer.original =
                buffer.current;


            buffer.dirty =
                false;


            renderTabs();

            renderEditor();

            renderFileTree();


            showToast(
                `${basename(path)} saved`
            );

        }


        function hasUnsavedFiles() {

            return Array
                .from(
                    editorBuffers
                        .values()
                )
                .some(
                    buffer =>
                        buffer.dirty
                );

        }


        // =========================================
        // CURSOR POSITION
        // =========================================

        function updateCursorPosition() {

            if (
                !activeFilePath
            ) {

                return;

            }


            const cursor =
                codeEditor.selectionStart;


            const beforeCursor =
                codeEditor.value
                    .slice(
                        0,
                        cursor
                    );


            const lines =
                beforeCursor
                    .split("\n");


            const line =
                lines.length;


            const column =
                lines[
                    lines.length - 1
                ].length
                +
                1;


            statusPosition.textContent =
                `Ln ${line}, Col ${column}`;

        }


        // =========================================
        // SEARCH
        // =========================================

        function collectProjectFiles(
            folderPath,
            collection = []
        ) {

            const entries =
                simulationState
                    .list(
                        folderPath
                    );


            entries.forEach(
                entry => {

                    if (
                        entry.type
                        ===
                        "folder"
                    ) {

                        collectProjectFiles(
                            entry.path,
                            collection
                        );

                    }
                    else if (
                        entry.type
                        ===
                        "file"
                    ) {

                        collection.push(
                            entry
                        );

                    }

                }
            );


            return collection;

        }


        function renderSearchResults() {

            searchResults.innerHTML =
                "";


            const query =
                searchInput.value
                    .trim()
                    .toLowerCase();


            if (
                !currentProjectPath
            ) {

                searchResults.innerHTML =
                    `
                    <div class="vscode-search-empty">
                        Open a project first.
                    </div>
                    `;

                return;

            }


            if (!query) {

                searchResults.innerHTML =
                    `
                    <div class="vscode-search-empty">
                        Search filenames or file contents.
                    </div>
                    `;

                return;

            }


            const files =
                collectProjectFiles(
                    currentProjectPath
                );


            const matches =
                files.filter(
                    file => {

                        const node =
                            simulationState
                                .read(
                                    file.path
                                );


                        const text =
                            [
                                file.name,
                                node?.content
                                ||
                                ""
                            ]
                                .join("\n")
                                .toLowerCase();


                        return text.includes(
                            query
                        );

                    }
                );


            if (
                matches.length
                === 0
            ) {

                searchResults.innerHTML =
                    `
                    <div class="vscode-search-empty">
                        No results found.
                    </div>
                    `;

                return;

            }


            matches.forEach(
                file => {

                    const node =
                        simulationState
                            .read(
                                file.path
                            );


                    const content =
                        node?.content
                        ||
                        "";


                    const lower =
                        content
                            .toLowerCase();


                    const matchIndex =
                        lower.indexOf(
                            query
                        );


                    let preview =
                        "";


                    if (
                        matchIndex !== -1
                    ) {

                        const start =
                            Math.max(
                                0,
                                matchIndex - 35
                            );


                        preview =
                            content
                                .slice(
                                    start,
                                    start + 120
                                )
                                .replaceAll(
                                    "\n",
                                    " "
                                );

                    }
                    else {

                        preview =
                            relativePath(
                                file.path
                            );

                    }


                    const button =
                        document.createElement(
                            "button"
                        );


                    button.type =
                        "button";


                    button.className =
                        "vscode-search-result";


                    button.innerHTML =
                        `
                        <strong>
                            ${relativePath(file.path)}
                        </strong>

                        <span>
                            ${preview}
                        </span>
                        `;


                    button.addEventListener(
                        "click",
                        () => {

                            openFile(
                                file.path
                            );

                        }
                    );


                    searchResults.appendChild(
                        button
                    );

                }
            );

        }


        function openSearch() {

            searchPanel.hidden =
                false;


            searchInput.focus();


            renderSearchResults();

        }


        function hideSearch() {

            searchPanel.hidden =
                true;


            searchInput.value =
                "";


            searchResults.innerHTML =
                "";

        }


        // =========================================
        // EVENTS
        // =========================================

        closeProjectButton.addEventListener(
            "click",
            closeProject
        );


        refreshProjectButton.addEventListener(
            "click",
            () => {

                renderProjectPicker();

                renderFileTree();

            }
        );


        codeEditor.addEventListener(
            "input",
            updateEditorBuffer
        );


        codeEditor.addEventListener(
            "click",
            updateCursorPosition
        );


        codeEditor.addEventListener(
            "keyup",
            updateCursorPosition
        );


        codeEditor.addEventListener(
            "scroll",
            () => {

                lineNumbers.scrollTop =
                    codeEditor.scrollTop;

            }
        );


        codeEditor.addEventListener(
            "keydown",
            event => {

                // Ctrl + S
                if (
                    event.ctrlKey
                    &&
                    event.key
                        .toLowerCase()
                        ===
                        "s"
                ) {

                    event.preventDefault();

                    saveFile();

                    return;

                }


                // Tab inserts spaces
                if (
                    event.key
                    ===
                    "Tab"
                ) {

                    event.preventDefault();


                    const start =
                        codeEditor.selectionStart;


                    const end =
                        codeEditor.selectionEnd;


                    const value =
                        codeEditor.value;


                    codeEditor.value =
                        value.substring(
                            0,
                            start
                        )
                        +
                        "    "
                        +
                        value.substring(
                            end
                        );


                    codeEditor.selectionStart =
                        codeEditor.selectionEnd =
                            start + 4;


                    updateEditorBuffer();

                }

            }
        );


        saveButton.addEventListener(
            "click",
            () => {

                saveFile();

            }
        );


        searchButton.addEventListener(
            "click",
            openSearch
        );


        closeSearch.addEventListener(
            "click",
            hideSearch
        );


        searchInput.addEventListener(
            "input",
            renderSearchResults
        );


        document.addEventListener(
            "keydown",
            event => {

                if (
                    event.ctrlKey
                    &&
                    event.key
                        .toLowerCase()
                        ===
                        "f"
                    &&
                    !app
                        .getAttribute(
                            "aria-hidden"
                        )
                        ?.includes(
                            "true"
                        )
                ) {

                    event.preventDefault();

                    openSearch();

                }

            }
        );


        window.addEventListener(
            "careergrid:filesystem-changed",
            () => {

                renderProjectPicker();

                if (
                    currentProjectPath
                ) {

                    renderFileTree();

                }

            }
        );


        // =========================================
        // INITIALIZE
        // =========================================

        renderProjectPicker();

        renderTabs();

        renderEditor();

    }
);