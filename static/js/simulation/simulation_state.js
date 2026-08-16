(() => {

    const workspace =
        document.getElementById(
            "careergrid-workspace"
        );


    const workspaceKey =
        workspace?.dataset.workspaceKey
        ||
        "default";


    const storageKey =
        `careergrid-simulation-state-${workspaceKey}`;


    // =========================================
    // HELPERS
    // =========================================

    function clone(value) {

        return JSON.parse(
            JSON.stringify(value)
        );

    }


    function normalizePath(path = "/") {

        let normalized =
            String(path)
                .replaceAll("\\", "/")
                .replace(/\/+/g, "/");


        if (!normalized.startsWith("/")) {

            normalized =
                "/" + normalized;

        }


        if (
            normalized.length > 1
            &&
            normalized.endsWith("/")
        ) {

            normalized =
                normalized.slice(
                    0,
                    -1
                );

        }


        return normalized;

    }


    function splitPath(path) {

        return normalizePath(path)
            .split("/")
            .filter(Boolean);

    }


    function baseName(path) {

        const parts =
            splitPath(path);

        return (
            parts[
                parts.length - 1
            ]
            ||
            "/"
        );

    }


    function parentPath(path) {

        const parts =
            splitPath(path);

        parts.pop();

        return (
            "/"
            +
            parts.join("/")
        )
            .replace(
                /^$/,
                "/"
            );

    }


    // =========================================
    // ATTACHMENT CATALOG
    //
    // These are the REAL simulated resources
    // behind Avery's attachments.
    // =========================================

    const attachmentCatalog = {

        "checkout-project": {

            id:
                "checkout-project",

            name:
                "checkout-service.zip",

            type:
                "archive",

            fileType:
                "ZIP archive",

            size:
                "18 KB",

            archiveEntries: {

                "checkout-service/README.md": {

                    type:
                        "file",

                    fileType:
                        "Markdown",

                    size:
                        "2 KB",

                    content:
`# Checkout Service

This service prepares and sends checkout requests to the commerce API.

## Running the project

Run the application and use the checkout endpoint to reproduce the reported failure.

## Testing

Tests are located in the tests directory.

Investigate the current checkout failure before changing unrelated code.`
                },


                "checkout-service/app.py": {

                    type:
                        "file",

                    fileType:
                        "Python",

                    size:
                        "3 KB",

                    content:
`from flask import Flask
from services.checkout_service import CheckoutService

app = Flask(__name__)

checkout_service = CheckoutService()


@app.route("/checkout", methods=["POST"])
def checkout():
    return checkout_service.checkout()


if __name__ == "__main__":
    app.run(debug=True)
`
                },


                "checkout-service/services/checkout_service.py": {

                    type:
                        "file",

                    fileType:
                        "Python",

                    size:
                        "4 KB",

                    content:
`class CheckoutService:

    def checkout(self):
        cart = self.get_cart()

        payload = {
            "user_id": cart["user_id"],
            "product": cart["product_id"],
            "quantity": cart["quantity"]
        }

        response = self.send_checkout_request(payload)

        return response


    def get_cart(self):
        return {
            "user_id": 1842,
            "product_id": 783,
            "quantity": 1
        }


    def send_checkout_request(self, payload):
        # Simulated external commerce API request
        return {
            "status": 400,
            "payload": payload
        }
`
                },


                "checkout-service/tests/test_checkout.py": {

                    type:
                        "file",

                    fileType:
                        "Python",

                    size:
                        "3 KB",

                    content:
`from services.checkout_service import CheckoutService


def test_cart_contains_product():
    service = CheckoutService()

    cart = service.get_cart()

    assert "product_id" in cart
    assert cart["quantity"] > 0
`
                },


                "checkout-service/.gitignore": {

                    type:
                        "file",

                    fileType:
                        "Git ignore",

                    size:
                        "1 KB",

                    content:
`.env
venv/
__pycache__/
*.pyc
`
                }

            }

        },


        "checkout-logs": {

            id:
                "checkout-logs",

            name:
                "checkout-error.log",

            type:
                "file",

            fileType:
                "Log file",

            size:
                "4 KB",

            content:
`2026-08-16 08:39:41 INFO  POST /checkout
2026-08-16 08:39:41 INFO  user_id=1842
2026-08-16 08:39:41 INFO  Sending request to commerce API

2026-08-16 08:39:42 ERROR Commerce API responded with 400 Bad Request
2026-08-16 08:39:42 ERROR Response body:
{
    "error": "validation_error",
    "message": "product_id is required"
}

2026-08-16 08:39:42 ERROR Checkout failed for user_id=1842
`
        }

    };


    // =========================================
    // INITIAL FILESYSTEM
    // =========================================

    function createInitialState() {

        return {

            version:
                2,

            filesystem: {

                Desktop: {

                    name:
                        "Desktop",

                    type:
                        "folder",

                    children:
                        {}

                },


                Downloads: {

                    name:
                        "Downloads",

                    type:
                        "folder",

                    children:
                        {}

                },


                Documents: {

                    name:
                        "Documents",

                    type:
                        "folder",

                    children:
                        {}

                },


                Projects: {

                    name:
                        "Projects",

                    type:
                        "folder",

                    children:
                        {}

                }

            },

            git: {

                repositories:
                    {}

            },

            terminal: {

                cwd:
                    "/Projects",

                history:
                    []

            }

        };

    }


    function loadState() {

        try {

            const stored =
                localStorage.getItem(
                    storageKey
                );


            if (stored) {

                const parsed =
                    JSON.parse(stored);


                if (
                    parsed
                    &&
                    parsed.filesystem
                ) {

                    // Upgrade older CareerGrid simulation states
                    // without destroying the user's files.

                    if (!parsed.git) {

                        parsed.git = {
                            repositories: {}
                        };

                    }


                    if (!parsed.git.repositories) {

                        parsed.git.repositories = {};

                    }


                    if (!parsed.terminal) {

                        parsed.terminal = {
                            cwd: "/Projects",
                            history: []
                        };

                    }


                    if (!Array.isArray(parsed.terminal.history)) {

                        parsed.terminal.history = [];

                    }


                    return parsed;

                }

            }

        }
        catch (error) {

            console.warn(
                "Could not load CareerGrid simulation state:",
                error
            );

        }


        return createInitialState();

    }


    let state =
        loadState();


    // =========================================
    // SAVE / EVENT
    // =========================================

    function emitChange() {

        window.dispatchEvent(
            new CustomEvent(
                "careergrid:filesystem-changed",
                {
                    detail: {
                        workspaceKey:
                            workspaceKey
                    }
                }
            )
        );

    }


    function saveState() {

        localStorage.setItem(
            storageKey,
            JSON.stringify(state)
        );


        emitChange();

    }


    // =========================================
    // NODE ACCESS
    // =========================================

    function getRoot() {

        return {

            name:
                "Home",

            type:
                "folder",

            children:
                state.filesystem

        };

    }


    function getNode(path = "/") {

        const normalized =
            normalizePath(path);


        if (normalized === "/") {

            return getRoot();

        }


        const parts =
            splitPath(normalized);


        let current =
            getRoot();


        for (
            const part
            of parts
        ) {

            if (
                current.type !== "folder"
                ||
                !current.children
                ||
                !current.children[part]
            ) {

                return null;

            }


            current =
                current.children[part];

        }


        return current;

    }


    function ensureFolder(
        path,
        persist = true
    ) {

        const parts =
            splitPath(path);


        let current =
            getRoot();


        for (
            const part
            of parts
        ) {

            if (!current.children) {

                current.children =
                    {};

            }


            if (!current.children[part]) {

                current.children[part] =
                    {
                        name:
                            part,

                        type:
                            "folder",

                        children:
                            {}
                    };

            }


            current =
                current.children[part];


            if (
                current.type
                !== "folder"
            ) {

                throw new Error(
                    `${part} is not a folder`
                );

            }

        }


        if (persist) {

            saveState();

        }


        return current;

    }


    function writeNode(
        path,
        node,
        persist = true
    ) {

        const normalized =
            normalizePath(path);


        const parent =
            ensureFolder(
                parentPath(
                    normalized
                ),
                false
            );


        const name =
            baseName(
                normalized
            );


        parent.children[name] =
            {
                ...clone(node),

                name:
                    name,

                modifiedAt:
                    node.modifiedAt
                    ||
                    new Date()
                        .toISOString()
            };


        if (persist) {

            saveState();

        }


        return parent.children[name];

    }


    // =========================================
    // PUBLIC FILE OPERATIONS
    // =========================================

    function exists(path) {

        return (
            getNode(path)
            !==
            null
        );

    }


    function list(path = "/") {

        const folder =
            getNode(path);


        if (
            !folder
            ||
            folder.type
            !== "folder"
        ) {

            return [];

        }


        return Object
            .entries(
                folder.children
                ||
                {}
            )
            .map(
                ([name, node]) => {

                    const childPath =
                        normalizePath(
                            `${path}/${name}`
                        );


                    return {

                        ...clone(node),

                        path:
                            childPath

                    };

                }
            );

    }


    function read(path) {

        const node =
            getNode(path);


        return node
            ?
            clone(node)
            :
            null;

    }


    // =========================================
    // OUTLOOK ATTACHMENTS
    // =========================================

    function saveAttachmentById(
        attachmentId
    ) {

        const attachment =
            attachmentCatalog[
                attachmentId
            ];


        if (!attachment) {

            console.warn(
                "Unknown attachment:",
                attachmentId
            );

            return false;

        }


        const destination =
            `/Downloads/${attachment.name}`;


        if (exists(destination)) {

            return true;

        }


        writeNode(
            destination,
            attachment
        );


        return true;

    }


    function hasDownloadedAttachment(
        attachmentId
    ) {

        const attachment =
            attachmentCatalog[
                attachmentId
            ];


        if (!attachment) {

            return false;

        }


        return exists(
            `/Downloads/${attachment.name}`
        );

    }


    // =========================================
    // ARCHIVE EXTRACTION
    // =========================================

    function extractArchive(
        archivePath,
        destination = "/Projects"
    ) {

        const archive =
            getNode(
                archivePath
            );


        if (
            !archive
            ||
            archive.type
            !== "archive"
            ||
            !archive.archiveEntries
        ) {

            return {
                success:
                    false,

                message:
                    "This file cannot be extracted."
            };

        }


        const entries =
            Object.entries(
                archive.archiveEntries
            );


        entries.forEach(
            ([relativePath, entry]) => {

                const fullPath =
                    normalizePath(
                        `${destination}/${relativePath}`
                    );


                writeNode(
                    fullPath,
                    entry,
                    false
                );

            }
        );


        saveState();


        const firstEntry =
            entries[0]?.[0]
            ||
            "";


        const projectRoot =
            firstEntry
                .split("/")[0];


        const projectPath =
            normalizePath(
                `${destination}/${projectRoot}`
            );


        // Every extracted project begins as its own
        // simulated Git repository.
        ensureRepository(
            projectPath
        );


        return {

            success:
                true,

            projectPath:
                projectPath

        };

    }
    // =========================================
    // GIT HELPERS
    // =========================================

    function createCommitId() {

        return (
            Date.now()
                .toString(16)
                .slice(-5)
            +
            Math.random()
                .toString(16)
                .slice(2, 5)
        );

    }


    function snapshotsEqual(
        first,
        second
    ) {

        if (
            !first
            ||
            !second
        ) {

            return false;

        }


        return (
            (first.content || "")
            ===
            (second.content || "")
        );

    }


    function snapshotProject(
        projectPath
    ) {

        const snapshot =
            {};


        function walk(
            folderPath
        ) {

            const entries =
                list(
                    folderPath
                );


            entries.forEach(
                entry => {

                    if (
                        entry.type
                        ===
                        "folder"
                    ) {

                        walk(
                            entry.path
                        );

                        return;

                    }


                    if (
                        entry.type
                        ===
                        "file"
                    ) {

                        const node =
                            read(
                                entry.path
                            );


                        snapshot[
                            normalizePath(
                                entry.path
                            )
                        ] =
                            clone(
                                node
                            );

                    }

                }
            );

        }


        walk(
            normalizePath(
                projectPath
            )
        );


        return snapshot;

    }


    function restoreProjectSnapshot(
        projectPath,
        snapshot
    ) {

        const project =
            getNode(
                projectPath
            );


        if (
            !project
            ||
            project.type
            !==
            "folder"
        ) {

            return false;

        }


        project.children =
            {};


        Object
            .entries(
                snapshot
            )
            .forEach(
                ([path, node]) => {

                    writeNode(
                        path,
                        node,
                        false
                    );

                }
            );


        saveState();


        return true;

    }


    // =========================================
    // REPOSITORY CREATION
    // =========================================

    function ensureRepository(
        projectPath
    ) {

        const normalized =
            normalizePath(
                projectPath
            );


        const project =
            getNode(
                normalized
            );


        if (
            !project
            ||
            project.type
            !==
            "folder"
        ) {

            return null;

        }


        if (
            state.git.repositories[
                normalized
            ]
        ) {

            return state.git.repositories[
                normalized
            ];

        }


        const initialSnapshot =
            snapshotProject(
                normalized
            );


        const initialCommit =
            {
                id:
                    createCommitId(),

                message:
                    "Initial project files",

                author:
                    "CareerGrid",

                timestamp:
                    new Date()
                        .toISOString(),

                snapshot:
                    clone(
                        initialSnapshot
                    )
            };


        const repository =
            {
                rootPath:
                    normalized,

                currentBranch:
                    "main",

                branches: {

                    main: {

                        name:
                            "main",

                        commits:
                            [
                                initialCommit
                            ],

                        headSnapshot:
                            clone(
                                initialSnapshot
                            )

                    }

                },

                staged:
                    {},

                remote: {

                    name:
                        "origin",

                    pushedBranches:
                        [
                            "main"
                        ],

                    branchHeads: {

                        main:
                            initialCommit.id

                    }

                }

            };


        state.git.repositories[
            normalized
        ] =
            repository;


        saveState();


        return repository;

    }


    function getRepository(
        projectPath
    ) {

        return (
            state.git.repositories[
                normalizePath(
                    projectPath
                )
            ]
            ||
            null
        );

    }


    function getRepositories() {

        return clone(
            state.git.repositories
        );

    }


    // =========================================
    // GIT STATUS
    // =========================================

    function gitStatus(
        projectPath
    ) {

        const repo =
            ensureRepository(
                projectPath
            );


        if (!repo) {

            return null;

        }


        const branch =
            repo.branches[
                repo.currentBranch
            ];


        const headSnapshot =
            branch.headSnapshot
            ||
            {};


        const workingSnapshot =
            snapshotProject(
                repo.rootPath
            );


        const staged =
            Object.keys(
                repo.staged
                ||
                {}
            );


        const modified =
            [];


        const untracked =
            [];


        const deleted =
            [];


        const allPaths =
            new Set(
                [
                    ...Object.keys(
                        headSnapshot
                    ),
                    ...Object.keys(
                        workingSnapshot
                    )
                ]
            );


        allPaths.forEach(
            path => {

                const headFile =
                    headSnapshot[
                        path
                    ];


                const workingFile =
                    workingSnapshot[
                        path
                    ];


                const stagedFile =
                    repo.staged[
                        path
                    ];


                if (
                    !headFile
                    &&
                    workingFile
                ) {

                    if (!stagedFile) {

                        untracked.push(
                            path
                        );

                    }

                    return;

                }


                if (
                    headFile
                    &&
                    !workingFile
                ) {

                    deleted.push(
                        path
                    );

                    return;

                }


                if (
                    headFile
                    &&
                    workingFile
                ) {

                    const comparison =
                        stagedFile
                        ||
                        headFile;


                    if (
                        !snapshotsEqual(
                            comparison,
                            workingFile
                        )
                    ) {

                        modified.push(
                            path
                        );

                    }

                }

            }
        );


        return {

            branch:
                repo.currentBranch,

            staged:
                staged,

            modified:
                modified,

            untracked:
                untracked,

            deleted:
                deleted,

            clean:
                (
                    staged.length === 0
                    &&
                    modified.length === 0
                    &&
                    untracked.length === 0
                    &&
                    deleted.length === 0
                )

        };

    }


    // =========================================
    // GIT BRANCH
    // =========================================

    function gitCreateBranch(
        projectPath,
        branchName
    ) {

        const repo =
            ensureRepository(
                projectPath
            );


        if (!repo) {

            return {
                success:
                    false,

                message:
                    "Not a Git repository."
            };

        }


        const cleanName =
            String(
                branchName
                ||
                ""
            )
                .trim();


        if (!cleanName) {

            return {
                success:
                    false,

                message:
                    "Branch name is required."
            };

        }


        if (
            !/^[A-Za-z0-9._/-]+$/
                .test(
                    cleanName
                )
        ) {

            return {
                success:
                    false,

                message:
                    "Invalid branch name."
            };

        }


        if (
            repo.branches[
                cleanName
            ]
        ) {

            return {
                success:
                    false,

                message:
                    `A branch named '${cleanName}' already exists.`
            };

        }


        const sourceBranch =
            repo.branches[
                repo.currentBranch
            ];


        repo.branches[
            cleanName
        ] =
            {
                name:
                    cleanName,

                commits:
                    clone(
                        sourceBranch.commits
                    ),

                headSnapshot:
                    clone(
                        sourceBranch.headSnapshot
                    )

            };


        repo.currentBranch =
            cleanName;


        repo.staged =
            {};


        saveState();


        return {

            success:
                true,

            branch:
                cleanName

        };

    }


    function gitSwitchBranch(
        projectPath,
        branchName
    ) {

        const repo =
            ensureRepository(
                projectPath
            );


        if (!repo) {

            return {
                success:
                    false,

                message:
                    "Not a Git repository."
            };

        }


        if (
            !repo.branches[
                branchName
            ]
        ) {

            return {
                success:
                    false,

                message:
                    `Branch '${branchName}' does not exist.`
            };

        }


        const status =
            gitStatus(
                projectPath
            );


        if (
            status
            &&
            !status.clean
        ) {

            return {
                success:
                    false,

                message:
                    "Commit or discard your changes before switching branches."
            };

        }


        repo.currentBranch =
            branchName;


        repo.staged =
            {};


        restoreProjectSnapshot(
            repo.rootPath,
            repo.branches[
                branchName
            ].headSnapshot
        );


        saveState();


        return {

            success:
                true,

            branch:
                branchName

        };

    }


    // =========================================
    // GIT ADD
    // =========================================

    function gitStage(
        projectPath,
        target = "."
    ) {

        const repo =
            ensureRepository(
                projectPath
            );


        if (!repo) {

            return {
                success:
                    false,

                message:
                    "Not a Git repository."
            };

        }


        const currentSnapshot =
            snapshotProject(
                repo.rootPath
            );


        const headSnapshot =
            repo.branches[
                repo.currentBranch
            ].headSnapshot;


        let paths =
            [];


        if (
            target === "."
            ||
            target === "-A"
            ||
            target === "--all"
        ) {

            paths =
                Object.keys(
                    currentSnapshot
                );

        }
        else {

            const normalizedTarget =
                normalizePath(
                    target
                );


            const targetNode =
                getNode(
                    normalizedTarget
                );


            if (!targetNode) {

                return {
                    success:
                        false,

                    message:
                        `pathspec '${target}' did not match any files`
                };

            }


            if (
                targetNode.type
                ===
                "folder"
            ) {

                paths =
                    Object.keys(
                        currentSnapshot
                    )
                        .filter(
                            path =>
                                path.startsWith(
                                    normalizedTarget
                                    + "/"
                                )
                        );

            }
            else {

                paths =
                    [
                        normalizedTarget
                    ];

            }

        }


        let stagedCount =
            0;


        paths.forEach(
            path => {

                const workingFile =
                    currentSnapshot[
                        path
                    ];


                const headFile =
                    headSnapshot[
                        path
                    ];


                if (
                    workingFile
                    &&
                    (
                        !headFile
                        ||
                        !snapshotsEqual(
                            headFile,
                            workingFile
                        )
                    )
                ) {

                    repo.staged[
                        path
                    ] =
                        clone(
                            workingFile
                        );


                    stagedCount += 1;

                }

            }
        );


        saveState();


        return {

            success:
                true,

            count:
                stagedCount

        };

    }


    // =========================================
    // GIT COMMIT
    // =========================================

    function gitCommit(
        projectPath,
        message,
        author = "CareerGrid User"
    ) {

        const repo =
            ensureRepository(
                projectPath
            );


        if (!repo) {

            return {
                success:
                    false,

                message:
                    "Not a Git repository."
            };

        }


        const stagedPaths =
            Object.keys(
                repo.staged
                ||
                {}
            );


        if (
            stagedPaths.length
            === 0
        ) {

            return {
                success:
                    false,

                message:
                    "nothing added to commit"
            };

        }


        const cleanMessage =
            String(
                message
                ||
                ""
            )
                .trim();


        if (!cleanMessage) {

            return {
                success:
                    false,

                message:
                    "Commit message is required."
            };

        }


        const branch =
            repo.branches[
                repo.currentBranch
            ];


        const nextSnapshot =
            clone(
                branch.headSnapshot
            );


        stagedPaths.forEach(
            path => {

                nextSnapshot[
                    path
                ] =
                    clone(
                        repo.staged[
                            path
                        ]
                    );

            }
        );


        const commit =
            {
                id:
                    createCommitId(),

                message:
                    cleanMessage,

                author:
                    author,

                timestamp:
                    new Date()
                        .toISOString(),

                snapshot:
                    clone(
                        nextSnapshot
                    )
            };


        branch.commits.push(
            commit
        );


        branch.headSnapshot =
            nextSnapshot;


        repo.staged =
            {};


        saveState();


        return {

            success:
                true,

            commit:
                clone(
                    commit
                ),

            branch:
                repo.currentBranch,

            filesChanged:
                stagedPaths.length

        };

    }


    // =========================================
    // GIT PUSH
    // =========================================

    function gitPush(
        projectPath
    ) {

        const repo =
            ensureRepository(
                projectPath
            );


        if (!repo) {

            return {
                success:
                    false,

                message:
                    "Not a Git repository."
            };

        }


        const branchName =
            repo.currentBranch;


        const branch =
            repo.branches[
                branchName
            ];


        const headCommit =
            branch.commits[
                branch.commits.length - 1
            ];


        if (
            !repo.remote.pushedBranches
                .includes(
                    branchName
                )
        ) {

            repo.remote.pushedBranches.push(
                branchName
            );

        }


        repo.remote.branchHeads[
            branchName
        ] =
            headCommit.id;


        saveState();


        return {

            success:
                true,

            branch:
                branchName,

            commit:
                headCommit.id

        };

    }


    // =========================================
    // GIT LOG
    // =========================================

    function gitLog(
        projectPath
    ) {

        const repo =
            ensureRepository(
                projectPath
            );


        if (!repo) {

            return [];

        }


        return clone(
            repo.branches[
                repo.currentBranch
            ].commits
        )
            .reverse();

    }


    // =========================================
    // TERMINAL SESSION
    // =========================================

    function getTerminalSession() {

        return clone(
            state.terminal
        );

    }


    function setTerminalCwd(
        path
    ) {

        state.terminal.cwd =
            normalizePath(
                path
            );


        saveState();

    }


    function recordTerminalCommand(
        command,
        output = ""
    ) {

        state.terminal.history.push(
            {
                command:
                    command,

                output:
                    output,

                timestamp:
                    new Date()
                        .toISOString()
            }
        );


        // Don't let development/testing create
        // thousands of stored entries.
        if (
            state.terminal.history.length
            >
            150
        ) {

            state.terminal.history =
                state.terminal.history
                    .slice(
                        -150
                    );

        }


        saveState();

    }


    function clearTerminalHistory() {

        state.terminal.history =
            [];


        saveState();

    }

    // =========================================
    // EXPOSE API
    // =========================================

    window.CareerGridSimulationState = {

        workspaceKey:
            workspaceKey,

        storageKey:
            storageKey,

        list:
            list,

        read:
            read,

        exists:
            exists,

        ensureFolder:
            ensureFolder,

        writeNode:
            writeNode,

        saveAttachmentById:
            saveAttachmentById,

        hasDownloadedAttachment:
            hasDownloadedAttachment,

        extractArchive:
            extractArchive,

        normalizePath:
            normalizePath,

        parentPath:
            parentPath,

        baseName:
            baseName,

        ensureRepository:
            ensureRepository,

        getRepository:
            getRepository,

        getRepositories:
            getRepositories,

        gitStatus:
            gitStatus,

        gitCreateBranch:
            gitCreateBranch,

        gitSwitchBranch:
            gitSwitchBranch,

        gitStage:
            gitStage,

        gitCommit:
            gitCommit,

        gitPush:
            gitPush,

        gitLog:
            gitLog,

        getTerminalSession:
            getTerminalSession,

        setTerminalCwd:
            setTerminalCwd,

        recordTerminalCommand:
            recordTerminalCommand,

        clearTerminalHistory:
            clearTerminalHistory

    };

})();