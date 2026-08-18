document.addEventListener(
    "DOMContentLoaded",
    () => {

        const app =
            document.getElementById(
                "github-app"
            );

        const simulationState =
            window.CareerGridSimulationState;

        const repositorySelect =
            document.getElementById(
                "github-repository-select"
            );

        const content =
            document.getElementById(
                "github-content"
            );

        const toast =
            document.getElementById(
                "github-toast"
            );

        if (
            !app
            ||
            !simulationState
            ||
            !repositorySelect
            ||
            !content
            ||
            !toast
        ) {

            return;

        }

        const userName =
            app.dataset.userName
            ||
            "CareerGrid User";

        let selectedRepositoryPath =
            "";

        let selectedBranch =
            "";

        let activeTab =
            "code";

        let currentDirectory =
            "";

        let selectedPullRequestId =
            null;

        let showPullRequestForm =
            false;


        function escapeHtml(
            value = ""
        ) {

            return String(value)
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");

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


        function repositories() {

            return simulationState
                .getRepositories();

        }


        function currentRepository() {

            return repositories()[
                selectedRepositoryPath
            ]
            ||
            null;

        }


        function repositoryName(
            repository
        ) {

            return simulationState
                .baseName(
                    repository.rootPath
                );

        }


        function isPushed(
            repository,
            branchName
        ) {

            return repository.remote.pushedBranches
                .includes(
                    branchName
                );

        }


        function formatTime(
            value
        ) {

            if (!value) {

                return "Unknown time";

            }

            return new Date(value)
                .toLocaleString();

        }


        function shortId(
            commit
        ) {

            return String(
                commit?.id
                ||
                ""
            )
                .slice(0, 7);

        }


        function branchOptions(
            repository,
            value
        ) {

            return Object.keys(
                repository.branches
            )
                .map(
                    branch =>
                        `<option value="${escapeHtml(branch)}" ${branch === value ? "selected" : ""}>${escapeHtml(branch)}</option>`
                )
                .join("");

        }


        function renderRepositorySelector() {

            const allRepositories =
                repositories();

            const paths =
                Object.keys(allRepositories)
                    .sort();

            if (
                !paths.includes(
                    selectedRepositoryPath
                )
            ) {

                selectedRepositoryPath =
                    paths[0]
                    ||
                    "";

                selectedBranch =
                    "";

                currentDirectory =
                    selectedRepositoryPath;

            }

            repositorySelect.innerHTML =
                paths.length
                    ?
                    paths.map(
                        path => {

                            const repository =
                                allRepositories[path];

                            return `<option value="${escapeHtml(path)}">careergrid-sim / ${escapeHtml(repositoryName(repository))}</option>`;

                        }
                    )
                        .join("")
                    :
                    '<option value="">No repositories</option>';

            repositorySelect.value =
                selectedRepositoryPath;

            repositorySelect.disabled =
                paths.length === 0;

        }


        function statusBadge(
            repository,
            branchName
        ) {

            return isPushed(
                repository,
                branchName
            )
                ?
                '<span class="github-status-badge is-pushed">Pushed</span>'
                :
                '<span class="github-status-badge is-local">Local only</span>';

        }


        function latestCommit(
            repository,
            branchName
        ) {

            const commits =
                repository.branches[
                    branchName
                ]?.commits
                ||
                [];

            return commits[
                commits.length - 1
            ]
            ||
            null;

        }


        function renderBranches(
            repository
        ) {

            return Object.keys(
                repository.branches
            )
                .sort()
                .map(
                    branch =>
                        `<div class="github-branch-row ${branch === repository.currentBranch ? "is-current" : ""}"><span class="github-branch-name">${branch === repository.currentBranch ? "● " : ""}${escapeHtml(branch)}</span>${statusBadge(repository, branch)}</div>`
                )
                .join("");

        }


        function renderCommits(
            repository,
            branchName,
            limit = null
        ) {

            let commits = [
                ...(
                    repository.branches[
                        branchName
                    ]?.commits
                    ||
                    []
                )
            ]
                .reverse();

            if (limit) {

                commits = commits.slice(
                    0,
                    limit
                );

            }

            return commits.length
                ?
                commits.map(
                    commit =>
                        `<div class="github-commit-row"><div><div class="github-commit-title">${escapeHtml(commit.message)}</div><div class="github-commit-meta">${escapeHtml(commit.author)} committed ${escapeHtml(formatTime(commit.timestamp))}</div></div><span class="github-commit-id">${escapeHtml(shortId(commit))}</span></div>`
                )
                    .join("")
                :
                '<p class="github-muted">No commits on this branch yet.</p>';

        }


        function pathLabel(
            path,
            rootPath
        ) {

            if (path === rootPath) {

                return "Repository files";

            }

            return path.replace(
                rootPath + "/",
                ""
            );

        }


        function renderFileList(
            repository
        ) {

            if (
                !currentDirectory.startsWith(
                    repository.rootPath
                )
            ) {

                currentDirectory =
                    repository.rootPath;

            }

            const entries =
                simulationState.list(
                    currentDirectory
                )
                    .sort(
                        (first, second) => {

                            if (first.type !== second.type) {

                                return first.type === "folder"
                                    ?
                                    -1
                                    :
                                    1;

                            }

                            return first.name.localeCompare(
                                second.name
                            );

                        }
                    );

            const parent =
                simulationState.parentPath(
                    currentDirectory
                );

            const canGoUp =
                currentDirectory !== repository.rootPath;

            return `
                <section class="github-section">
                    <div class="github-section-body">
                        <div class="github-actions">
                            <strong>${escapeHtml(pathLabel(currentDirectory, repository.rootPath))}</strong>
                            ${canGoUp ? '<button class="github-secondary-button" type="button" data-github-action="up-directory">Up</button>' : ""}
                        </div>
                        ${entries.length ? entries.map(entry => `<div class="github-file-row"><span class="github-file-icon">${entry.type === "folder" ? "DIR" : "FILE"}</span><button class="github-file-button" type="button" data-github-path="${escapeHtml(entry.path)}" data-github-node-type="${escapeHtml(entry.type)}">${escapeHtml(entry.name)}${entry.type === "folder" ? "/" : ""}</button><span class="github-file-meta">${escapeHtml(entry.fileType || "Folder")}</span></div>`).join("") : '<p class="github-muted">This folder is empty.</p>'}
                        <input type="hidden" value="${escapeHtml(parent)}">
                    </div>
                </section>`;

        }


        function renderCodeTab(
            repository
        ) {

            const commit =
                latestCommit(
                    repository,
                    selectedBranch
                );

            return `
                <div class="github-actions">
                    <label>Branch <select class="github-branch-select" data-github-action="select-branch">${branchOptions(repository, selectedBranch)}</select></label>
                    <button class="github-primary-button" type="button" data-github-action="show-pr-form">Create Pull Request</button>
                </div>
                <div class="github-layout">
                    <div>
                        ${commit ? `<section class="github-section"><div class="github-section-body"><div class="github-commit-title">${escapeHtml(commit.message)}</div><div class="github-commit-meta">${escapeHtml(commit.author)} committed ${escapeHtml(formatTime(commit.timestamp))} · ${escapeHtml(shortId(commit))}</div></div></section>` : ""}
                        <div class="github-file-preview" id="github-file-preview"></div>
                        ${renderFileList(repository)}
                    </div>
                    <div><aside class="github-section"><h3 class="github-section-title">Branches</h3><div class="github-section-body github-branch-list">${renderBranches(repository)}</div></aside><aside class="github-section" style="margin-top: 16px;"><h3 class="github-section-title">Commits</h3><div class="github-section-body">${renderCommits(repository, selectedBranch, 5)}</div></aside></div>
                </div>`;

        }


        function renderPullRequestForm(
            repository
        ) {

            const compareBranch =
                selectedBranch;

            const baseBranch =
                repository.branches.main
                    ?
                    "main"
                    :
                    repository.currentBranch;

            return `
                <form class="github-pr-form" id="github-pr-form">
                    <div class="github-actions"><h3>Create pull request</h3><button class="github-secondary-button" type="button" data-github-action="cancel-pr-form">Cancel</button></div>
                    <div class="github-form-grid">
                        <label class="github-form-field">Base branch<select class="github-form-control" name="baseBranch">${branchOptions(repository, baseBranch)}</select></label>
                        <label class="github-form-field">Compare branch<select class="github-form-control" name="compareBranch">${branchOptions(repository, compareBranch)}</select></label>
                        <label class="github-form-field is-full">Title<input class="github-form-control" name="title" required maxlength="140" autocomplete="off"></label>
                        <label class="github-form-field is-full">Description<textarea class="github-form-control" name="description" rows="7" placeholder="Describe the change and any relevant context."></textarea></label>
                    </div>
                    <p class="github-form-error" id="github-pr-form-error"></p>
                    <div class="github-form-actions"><button class="github-primary-button" type="submit">Create Pull Request</button></div>
                </form>`;

        }


        function renderPullRequestDetail(
            repository,
            pullRequest
        ) {

            const commits =
                repository.branches[
                    pullRequest.compareBranch
                ]?.commits
                ||
                [];

            return `
                <section class="github-pr-detail">
                    <div class="github-actions"><div><h3>#${pullRequest.id} ${escapeHtml(pullRequest.title)}</h3><div class="github-detail-meta"><span class="github-status-badge is-open">Open</span><span>${escapeHtml(pullRequest.compareBranch)} → ${escapeHtml(pullRequest.baseBranch)}</span><span>opened by ${escapeHtml(pullRequest.author)} ${escapeHtml(formatTime(pullRequest.createdAt))}</span></div></div><button class="github-secondary-button" type="button" data-github-action="back-to-prs">Back to Pull Requests</button></div>
                    <p class="github-pr-description">${escapeHtml(pullRequest.description || "No description provided.")}</p>
                    <a class="github-pr-url" href="${escapeHtml(pullRequest.url)}" target="_blank" rel="noopener">${escapeHtml(pullRequest.url)}</a>
                    <div class="github-form-actions"><button class="github-secondary-button" type="button" data-github-action="copy-pr-link" data-github-url="${escapeHtml(pullRequest.url)}">Copy PR Link</button></div>
                    <section class="github-section"><h4 class="github-section-title">Compare branch commits</h4><div class="github-section-body">${renderCommits(repository, pullRequest.compareBranch)}</div></section>
                </section>`;

        }


        function renderPullRequestsTab(
            repository
        ) {

            const pullRequests =
                simulationState.getPullRequests(
                    repository.rootPath
                )
                    .sort(
                        (first, second) =>
                            second.id - first.id
                    );

            if (
                selectedPullRequestId !== null
            ) {

                const selectedPullRequest =
                    pullRequests.find(
                        pullRequest =>
                            pullRequest.id === selectedPullRequestId
                    );

                if (selectedPullRequest) {

                    return renderPullRequestDetail(
                        repository,
                        selectedPullRequest
                    );

                }

            }

            if (showPullRequestForm) {

                return renderPullRequestForm(
                    repository
                );

            }

            return `
                <div class="github-actions"><span class="github-muted">${pullRequests.length} pull request${pullRequests.length === 1 ? "" : "s"}</span><button class="github-primary-button" type="button" data-github-action="show-pr-form">Create Pull Request</button></div>
                <section class="github-section" style="margin-top: 16px;"><div class="github-section-body">${pullRequests.length ? pullRequests.map(pullRequest => `<div class="github-pr-row"><div><button class="github-link-button github-pr-title" type="button" data-github-pr-id="${pullRequest.id}">#${pullRequest.id} ${escapeHtml(pullRequest.title)}</button><div class="github-pr-meta">${escapeHtml(pullRequest.compareBranch)} → ${escapeHtml(pullRequest.baseBranch)} · opened by ${escapeHtml(pullRequest.author)}</div></div><span class="github-status-badge is-open">Open</span></div>`).join("") : '<p class="github-muted">No pull requests yet. Push a branch, then open a pull request here.</p>'}</div></section>`;

        }


        function render() {

            renderRepositorySelector();

            const repository =
                currentRepository();

            if (!repository) {

                content.innerHTML =
                    '<div class="github-empty-state"><strong>No repositories available.</strong><span>Download and extract a project first.</span></div>';

                return;

            }

            if (
                !repository.branches[
                    selectedBranch
                ]
            ) {

                selectedBranch =
                    repository.currentBranch;

            }

            content.innerHTML = `
                <div class="github-repository-page">
                    <header class="github-repository-header"><h2 class="github-repository-name">careergrid-sim / ${escapeHtml(repositoryName(repository))}</h2><p class="github-repository-path">${escapeHtml(repository.rootPath)}</p></header>
                    <nav class="github-tabs" aria-label="Repository navigation"><button class="github-tab ${activeTab === "code" ? "is-active" : ""}" type="button" data-github-tab="code">Code</button><button class="github-tab ${activeTab === "pulls" ? "is-active" : ""}" type="button" data-github-tab="pulls">Pull Requests</button></nav>
                    ${activeTab === "pulls" ? renderPullRequestsTab(repository) : renderCodeTab(repository)}
                </div>`;

        }


        function showFilePreview(
            path
        ) {

            const preview =
                document.getElementById(
                    "github-file-preview"
                );

            const node =
                simulationState.read(
                    path
                );

            if (
                !preview
                ||
                !node
                ||
                node.type === "folder"
            ) {

                return;

            }

            preview.innerHTML = `<section class="github-section"><h3 class="github-section-title">${escapeHtml(node.name)}</h3><div class="github-section-body"><pre>${escapeHtml(node.content || "")}</pre></div></section>`;

        }


        async function copyPullRequestLink(
            url
        ) {

            try {

                await navigator.clipboard.writeText(
                    url
                );

                showToast(
                    "Pull request link copied"
                );

            }
            catch (error) {

                window.prompt(
                    "Copy this pull request link:",
                    url
                );

            }

        }


        repositorySelect.addEventListener(
            "change",
            () => {

                selectedRepositoryPath =
                    repositorySelect.value;

                selectedBranch =
                    "";

                currentDirectory =
                    selectedRepositoryPath;

                selectedPullRequestId =
                    null;

                showPullRequestForm =
                    false;

                render();

            }
        );


        content.addEventListener(
            "change",
            event => {

                if (
                    event.target.matches(
                        '[data-github-action="select-branch"]'
                    )
                ) {

                    selectedBranch =
                        event.target.value;

                    render();

                }

            }
        );


        content.addEventListener(
            "click",
            event => {

                const tab =
                    event.target.closest(
                        "[data-github-tab]"
                    );

                if (tab) {

                    activeTab =
                        tab.dataset.githubTab;

                    selectedPullRequestId =
                        null;

                    showPullRequestForm =
                        false;

                    render();

                    return;

                }

                const file =
                    event.target.closest(
                        "[data-github-path]"
                    );

                if (file) {

                    if (
                        file.dataset.githubNodeType
                        === "folder"
                    ) {

                        currentDirectory =
                            file.dataset.githubPath;

                        render();

                    }
                    else {

                        showFilePreview(
                            file.dataset.githubPath
                        );

                    }

                    return;

                }

                const pullRequest =
                    event.target.closest(
                        "[data-github-pr-id]"
                    );

                if (pullRequest) {

                    selectedPullRequestId =
                        Number(
                            pullRequest.dataset.githubPrId
                        );

                    render();

                    return;

                }

                const action =
                    event.target.closest(
                        "[data-github-action]"
                    );

                if (!action) {

                    return;

                }

                if (
                    action.dataset.githubAction
                    === "up-directory"
                ) {

                    currentDirectory =
                        simulationState.parentPath(
                            currentDirectory
                        );

                    render();

                }

                if (
                    action.dataset.githubAction
                    === "show-pr-form"
                ) {

                    const repository =
                        currentRepository();

                    if (
                        app.dataset.positionId === "frontend-developer"
                        && repository
                        && Object.keys(repository.branches).length === 1
                        && repository.branches.main
                    ) {

                        const branchResult =
                            simulationState.gitCreateBranch(
                                repository.rootPath,
                                "fix/buy-now-checkout"
                            );

                        if (branchResult.success) {

                            selectedBranch =
                                branchResult.branch;

                        }

                    }

                    activeTab = "pulls";
                    showPullRequestForm = true;
                    selectedPullRequestId = null;
                    render();

                }

                if (
                    action.dataset.githubAction
                    === "cancel-pr-form"
                ) {

                    showPullRequestForm = false;
                    render();

                }

                if (
                    action.dataset.githubAction
                    === "back-to-prs"
                ) {

                    selectedPullRequestId = null;
                    render();

                }

                if (
                    action.dataset.githubAction
                    === "copy-pr-link"
                ) {

                    copyPullRequestLink(
                        action.dataset.githubUrl
                    );

                }

            }
        );


        content.addEventListener(
            "submit",
            event => {

                if (
                    event.target.id
                    !== "github-pr-form"
                ) {

                    return;

                }

                event.preventDefault();

                const form =
                    new FormData(
                        event.target
                    );

                const repository =
                    currentRepository();

                const result =
                    simulationState.createPullRequest(
                        repository.rootPath,
                        {
                            baseBranch: form.get("baseBranch"),
                            compareBranch: form.get("compareBranch"),
                            title: form.get("title"),
                            description: form.get("description"),
                            author: userName
                        }
                    );

                if (!result.success) {

                    const error =
                        document.getElementById(
                            "github-pr-form-error"
                        );

                    if (error) {

                        error.textContent =
                            result.message;

                    }

                    return;

                }

                showPullRequestForm = false;
                selectedPullRequestId =
                    result.pullRequest.id;

                activeTab = "pulls";

                render();

                showToast(
                    "Pull request created"
                );

            }
        );


        window.addEventListener(
            "careergrid:filesystem-changed",
            render
        );


        render();

    }
);
