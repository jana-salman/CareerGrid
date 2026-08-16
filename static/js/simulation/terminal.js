document.addEventListener(
    "DOMContentLoaded",
    () => {

        const app =
            document.getElementById(
                "terminal-app"
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


        const userName =
            app.dataset.userName
            ||
            "CareerGrid User";


        // =========================================
        // ELEMENTS
        // =========================================

        const screen =
            document.getElementById(
                "terminal-screen"
            );


        const historyElement =
            document.getElementById(
                "terminal-history"
            );


        const input =
            document.getElementById(
                "terminal-input"
            );


        const prompt =
            document.getElementById(
                "terminal-prompt"
            );


        const workingDirectory =
            document.getElementById(
                "terminal-working-directory"
            );


        // =========================================
        // SESSION
        // =========================================

        const savedSession =
            simulationState
                .getTerminalSession();


        let cwd =
            savedSession.cwd
            ||
            "/Projects";


        let commandHistory =
            savedSession.history
                .map(
                    entry =>
                        entry.command
                )
                .filter(Boolean);


        let commandHistoryIndex =
            commandHistory.length;


        // =========================================
        // PATH HELPERS
        // =========================================

        function normalizePath(
            path
        ) {

            return simulationState
                .normalizePath(
                    path
                );

        }


        function resolvePath(
            value = "."
        ) {

            const raw =
                String(
                    value
                    ||
                    "."
                );


            if (
                raw === "~"
            ) {

                return "/Projects";

            }


            const initial =
                raw.startsWith("/")
                    ?
                    raw
                    :
                    `${cwd}/${raw}`;


            const parts =
                initial
                    .replaceAll(
                        "\\",
                        "/"
                    )
                    .split("/");


            const resolved =
                [];


            parts.forEach(
                part => {

                    if (
                        !part
                        ||
                        part === "."
                    ) {

                        return;

                    }


                    if (
                        part === ".."
                    ) {

                        resolved.pop();

                        return;

                    }


                    resolved.push(
                        part
                    );

                }
            );


            return (
                "/"
                +
                resolved.join("/")
            );

        }


        function relativeToRepo(
            path,
            repoRoot
        ) {

            return path
                .replace(
                    repoRoot + "/",
                    ""
                );

        }


        // =========================================
        // REPOSITORY DISCOVERY
        // =========================================

        function projectRootForPath(
            path = cwd
        ) {

            const parts =
                normalizePath(
                    path
                )
                    .split("/")
                    .filter(Boolean);


            if (
                parts[0]
                !==
                "Projects"
                ||
                !parts[1]
            ) {

                return null;

            }


            return (
                "/Projects/"
                +
                parts[1]
            );

        }


        function currentRepository() {

            const projectRoot =
                projectRootForPath();


            if (!projectRoot) {

                return null;

            }


            return simulationState
                .ensureRepository(
                    projectRoot
                );

        }


        // =========================================
        // DISPLAY
        // =========================================

        function shortCwd() {

            if (
                cwd === "/Projects"
            ) {

                return "~/Projects";

            }


            if (
                cwd.startsWith(
                    "/Projects/"
                )
            ) {

                return (
                    "~/Projects/"
                    +
                    cwd
                        .slice(
                            "/Projects/"
                                .length
                        )
                );

            }


            return cwd;

        }


        function updatePrompt() {

            const repo =
                currentRepository();


            const branch =
                repo
                    ?
                    repo.currentBranch
                    :
                    null;


            prompt.textContent =
                branch
                    ?
                    `careergrid:${shortCwd()} (${branch})$`
                    :
                    `careergrid:${shortCwd()}$`;


            workingDirectory.textContent =
                cwd;

        }


        function scrollBottom() {

            screen.scrollTop =
                screen.scrollHeight;

        }


        function appendCommand(
            command,
            output = "",
            type = ""
        ) {

            const block =
                document.createElement(
                    "div"
                );


            block.className =
                "terminal-command-block";


            const line =
                document.createElement(
                    "div"
                );


            line.className =
                "terminal-command-line";


            const commandPrompt =
                document.createElement(
                    "span"
                );


            commandPrompt.className =
                "terminal-command-prompt";


            commandPrompt.textContent =
                prompt.textContent;


            const commandText =
                document.createElement(
                    "span"
                );


            commandText.className =
                "terminal-command-text";


            commandText.textContent =
                command;


            line.appendChild(
                commandPrompt
            );


            line.appendChild(
                commandText
            );


            block.appendChild(
                line
            );


            if (output) {

                const outputElement =
                    document.createElement(
                        "div"
                    );


                outputElement.className =
                    "terminal-output";


                if (type) {

                    outputElement.classList.add(
                        `is-${type}`
                    );

                }


                outputElement.textContent =
                    output;


                block.appendChild(
                    outputElement
                );

            }


            historyElement.appendChild(
                block
            );


            scrollBottom();

        }


        // =========================================
        // COMMAND TOKENIZER
        // =========================================

        function tokenize(
            command
        ) {

            const tokens =
                [];


            const regex =
                /"([^"]*)"|'([^']*)'|[^\s]+/g;


            let match;


            while (
                (
                    match =
                        regex.exec(
                            command
                        )
                )
            ) {

                tokens.push(
                    match[1]
                    ??
                    match[2]
                    ??
                    match[0]
                );

            }


            return tokens;

        }


        // =========================================
        // SHELL COMMANDS
        // =========================================

        function commandPwd() {

            return {
                output:
                    cwd
            };

        }


        function commandLs(
            args
        ) {

            const target =
                resolvePath(
                    args[0]
                    ||
                    "."
                );


            const node =
                simulationState
                    .read(
                        target
                    );


            if (!node) {

                return {
                    output:
                        `ls: cannot access '${args[0] || target}': No such file or directory`,

                    type:
                        "error"
                };

            }


            if (
                node.type
                !==
                "folder"
            ) {

                return {
                    output:
                        node.name
                };

            }


            const entries =
                simulationState
                    .list(
                        target
                    );


            if (
                entries.length
                ===
                0
            ) {

                return {
                    output:
                        ""
                };

            }


            const output =
                entries
                    .sort(
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
                    )
                    .map(
                        entry =>
                            entry.type
                            ===
                            "folder"
                                ?
                                entry.name + "/"
                                :
                                entry.name
                    )
                    .join(
                        "    "
                    );


            return {
                output:
                    output
            };

        }


        function commandCd(
            args
        ) {

            const destination =
                resolvePath(
                    args[0]
                    ||
                    "/Projects"
                );


            const node =
                simulationState
                    .read(
                        destination
                    );


            if (!node) {

                return {
                    output:
                        `cd: ${args[0] || destination}: No such file or directory`,

                    type:
                        "error"
                };

            }


            if (
                node.type
                !==
                "folder"
            ) {

                return {
                    output:
                        `cd: ${args[0]}: Not a directory`,

                    type:
                        "error"
                };

            }


            cwd =
                destination;


            simulationState
                .setTerminalCwd(
                    cwd
                );


            updatePrompt();


            return {
                output:
                    ""
            };

        }


        function commandCat(
            args
        ) {

            if (!args[0]) {

                return {
                    output:
                        "cat: missing file operand",

                    type:
                        "error"
                };

            }


            const path =
                resolvePath(
                    args[0]
                );


            const node =
                simulationState
                    .read(
                        path
                    );


            if (!node) {

                return {
                    output:
                        `cat: ${args[0]}: No such file or directory`,

                    type:
                        "error"
                };

            }


            if (
                node.type
                ===
                "folder"
            ) {

                return {
                    output:
                        `cat: ${args[0]}: Is a directory`,

                    type:
                        "error"
                };

            }


            return {
                output:
                    node.content
                    ||
                    ""
            };

        }


        // =========================================
        // GIT STATUS OUTPUT
        // =========================================

        function gitStatusOutput(
            repoRoot
        ) {

            const status =
                simulationState
                    .gitStatus(
                        repoRoot
                    );


            if (!status) {

                return {
                    output:
                        "fatal: not a git repository",

                    type:
                        "error"
                };

            }


            let output =
                `On branch ${status.branch}\n`;


            if (
                status.clean
            ) {

                output +=
                    "\nnothing to commit, working tree clean";


                return {
                    output:
                        output
                };

            }


            if (
                status.staged.length
                >
                0
            ) {

                output +=
                    "\n\nChanges to be committed:\n";


                status.staged
                    .forEach(
                        path => {

                            output +=
                                `  modified:   ${relativeToRepo(path, repoRoot)}\n`;

                        }
                    );

            }


            if (
                status.modified.length
                >
                0
            ) {

                output +=
                    "\n\nChanges not staged for commit:\n";


                status.modified
                    .forEach(
                        path => {

                            output +=
                                `  modified:   ${relativeToRepo(path, repoRoot)}\n`;

                        }
                    );

            }


            if (
                status.untracked.length
                >
                0
            ) {

                output +=
                    "\n\nUntracked files:\n";


                status.untracked
                    .forEach(
                        path => {

                            output +=
                                `  ${relativeToRepo(path, repoRoot)}\n`;

                        }
                    );

            }


            return {
                output:
                    output.trimEnd()
            };

        }


        // =========================================
        // GIT COMMAND
        // =========================================

        function commandGit(
            args
        ) {

            const repoRoot =
                projectRootForPath();


            if (!repoRoot) {

                return {
                    output:
                        "fatal: not a git repository (or any of the parent directories): .git",

                    type:
                        "error"
                };

            }


            const repo =
                simulationState
                    .ensureRepository(
                        repoRoot
                    );


            if (!repo) {

                return {
                    output:
                        "fatal: not a git repository",

                    type:
                        "error"
                };

            }


            const subcommand =
                args[0]
                ||
                "";


            // -------------------------
            // git status
            // -------------------------

            if (
                subcommand
                ===
                "status"
            ) {

                return gitStatusOutput(
                    repoRoot
                );

            }


            // -------------------------
            // git branch
            // -------------------------

            if (
                subcommand
                ===
                "branch"
            ) {

                const refreshed =
                    simulationState
                        .getRepository(
                            repoRoot
                        );


                const branches =
                    Object.keys(
                        refreshed.branches
                    );


                return {

                    output:
                        branches
                            .map(
                                branch =>
                                    branch
                                    ===
                                    refreshed.currentBranch
                                        ?
                                        `* ${branch}`
                                        :
                                        `  ${branch}`
                            )
                            .join("\n")

                };

            }


            // -------------------------
            // git switch
            // -------------------------

            if (
                subcommand
                ===
                "switch"
            ) {

                if (
                    args[1]
                    ===
                    "-c"
                ) {

                    const branchName =
                        args[2];


                    if (!branchName) {

                        return {
                            output:
                                "fatal: missing branch name",

                            type:
                                "error"
                        };

                    }


                    const result =
                        simulationState
                            .gitCreateBranch(
                                repoRoot,
                                branchName
                            );


                    updatePrompt();


                    return result.success
                        ?
                        {
                            output:
                                `Switched to a new branch '${result.branch}'`,

                            type:
                                "success"
                        }
                        :
                        {
                            output:
                                `fatal: ${result.message}`,

                            type:
                                "error"
                        };

                }


                const branchName =
                    args[1];


                if (!branchName) {

                    return {
                        output:
                            "fatal: missing branch name",

                        type:
                            "error"
                    };

                }


                const result =
                    simulationState
                        .gitSwitchBranch(
                            repoRoot,
                            branchName
                        );


                updatePrompt();


                return result.success
                    ?
                    {
                        output:
                            `Switched to branch '${result.branch}'`,

                        type:
                            "success"
                    }
                    :
                    {
                        output:
                            `error: ${result.message}`,

                        type:
                            "error"
                    };

            }


            // -------------------------
            // git checkout -b
            // -------------------------

            if (
                subcommand
                ===
                "checkout"
                &&
                args[1]
                ===
                "-b"
            ) {

                const branchName =
                    args[2];


                const result =
                    simulationState
                        .gitCreateBranch(
                            repoRoot,
                            branchName
                        );


                updatePrompt();


                return result.success
                    ?
                    {
                        output:
                            `Switched to a new branch '${result.branch}'`,

                        type:
                            "success"
                    }
                    :
                    {
                        output:
                            `fatal: ${result.message}`,

                        type:
                            "error"
                    };

            }


            // -------------------------
            // git add
            // -------------------------

            if (
                subcommand
                ===
                "add"
            ) {

                const target =
                    args[1]
                    ||
                    ".";


                let resolvedTarget =
                    target;


                if (
                    target !== "."
                    &&
                    target !== "-A"
                    &&
                    target !== "--all"
                ) {

                    resolvedTarget =
                        resolvePath(
                            target
                        );

                }


                const result =
                    simulationState
                        .gitStage(
                            repoRoot,
                            resolvedTarget
                        );


                return result.success
                    ?
                    {
                        output:
                            result.count > 0
                                ?
                                `Staged ${result.count} file(s).`
                                :
                                "No changes added.",

                        type:
                            result.count > 0
                                ?
                                "success"
                                :
                                "muted"
                    }
                    :
                    {
                        output:
                            `fatal: ${result.message}`,

                        type:
                            "error"
                    };

            }


            // -------------------------
            // git commit -m
            // -------------------------

            if (
                subcommand
                ===
                "commit"
            ) {

                const messageFlagIndex =
                    args.indexOf(
                        "-m"
                    );


                if (
                    messageFlagIndex
                    ===
                    -1
                    ||
                    !args[
                        messageFlagIndex
                        +
                        1
                    ]
                ) {

                    return {
                        output:
                            'error: commit message required. Use git commit -m "message"',

                        type:
                            "error"
                    };

                }


                const message =
                    args[
                        messageFlagIndex
                        +
                        1
                    ];


                const result =
                    simulationState
                        .gitCommit(
                            repoRoot,
                            message,
                            userName
                        );


                if (!result.success) {

                    return {
                        output:
                            result.message,

                        type:
                            "error"
                    };

                }


                return {

                    output:
`[${result.branch} ${result.commit.id}] ${result.commit.message}
 ${result.filesChanged} file(s) changed`,

                    type:
                        "success"

                };

            }


            // -------------------------
            // git push
            // -------------------------

            if (
                subcommand
                ===
                "push"
            ) {

                const result =
                    simulationState
                        .gitPush(
                            repoRoot
                        );


                return result.success
                    ?
                    {

                        output:
`Enumerating objects: done.
Writing objects: done.
To github.com/careergrid-sim/${simulationState.baseName(repoRoot)}.git
 * [new branch]      ${result.branch} -> ${result.branch}`,

                        type:
                            "success"

                    }
                    :
                    {
                        output:
                            result.message,

                        type:
                            "error"
                    };

            }


            // -------------------------
            // git log
            // -------------------------

            if (
                subcommand
                ===
                "log"
            ) {

                const commits =
                    simulationState
                        .gitLog(
                            repoRoot
                        );


                if (
                    args.includes(
                        "--oneline"
                    )
                ) {

                    return {

                        output:
                            commits
                                .map(
                                    commit =>
                                        `${commit.id} ${commit.message}`
                                )
                                .join("\n")

                    };

                }


                return {

                    output:
                        commits
                            .map(
                                commit =>
`commit ${commit.id}
Author: ${commit.author}
Date:   ${new Date(commit.timestamp).toLocaleString()}

    ${commit.message}`
                            )
                            .join(
                                "\n\n"
                            )

                };

            }


            return {
                output:
                    `git: '${subcommand}' is not supported in this CareerGrid workspace yet.`,

                type:
                    "error"
            };

        }


        // =========================================
        // HELP
        // =========================================

        function commandHelp() {

            return {

                output:
`Available commands:

Navigation
  pwd
  ls [path]
  cd <path>
  cat <file>
  clear

Git
  git status
  git branch
  git switch -c <branch>
  git switch <branch>
  git checkout -b <branch>
  git add <file>
  git add .
  git commit -m "message"
  git log
  git log --oneline
  git push

Terminal
  help`

            };

        }


        // =========================================
        // EXECUTE COMMAND
        // =========================================

        function executeCommand(
            rawCommand
        ) {

            const trimmed =
                rawCommand.trim();


            if (!trimmed) {

                return;

            }


            const tokens =
                tokenize(
                    trimmed
                );


            const command =
                (
                    tokens.shift()
                    ||
                    ""
                )
                    .toLowerCase();


            let result;


            switch (
                command
            ) {

                case "pwd":

                    result =
                        commandPwd();

                    break;


                case "ls":

                    result =
                        commandLs(
                            tokens
                        );

                    break;


                case "cd":

                    result =
                        commandCd(
                            tokens
                        );

                    break;


                case "cat":

                    result =
                        commandCat(
                            tokens
                        );

                    break;


                case "git":

                    result =
                        commandGit(
                            tokens
                        );

                    break;


                case "help":

                    result =
                        commandHelp();

                    break;


                case "clear":

                    historyElement.innerHTML =
                        "";


                    simulationState
                        .clearTerminalHistory();


                    return;


                default:

                    result =
                        {
                            output:
                                `${command}: command not found`,

                            type:
                                "error"
                        };

            }


            appendCommand(
                trimmed,
                result.output
                ||
                "",
                result.type
                ||
                ""
            );


            simulationState
                .recordTerminalCommand(
                    trimmed,
                    result.output
                    ||
                    ""
                );


            commandHistory.push(
                trimmed
            );


            commandHistoryIndex =
                commandHistory.length;


            updatePrompt();

        }


        // =========================================
        // RESTORE TERMINAL HISTORY
        // =========================================

        function restoreHistory() {

            const session =
                simulationState
                    .getTerminalSession();


            session.history
                .forEach(
                    entry => {

                        appendCommand(
                            entry.command,
                            entry.output
                            ||
                            ""
                        );

                    }
                );

        }


        // =========================================
        // EVENTS
        // =========================================

        input.addEventListener(
            "keydown",
            event => {

                if (
                    event.key
                    ===
                    "Enter"
                ) {

                    event.preventDefault();


                    const command =
                        input.value;


                    input.value =
                        "";


                    executeCommand(
                        command
                    );


                    return;

                }


                if (
                    event.key
                    ===
                    "ArrowUp"
                ) {

                    event.preventDefault();


                    if (
                        commandHistory.length
                        ===
                        0
                    ) {

                        return;

                    }


                    commandHistoryIndex =
                        Math.max(
                            0,
                            commandHistoryIndex
                            -
                            1
                        );


                    input.value =
                        commandHistory[
                            commandHistoryIndex
                        ]
                        ||
                        "";


                    input.setSelectionRange(
                        input.value.length,
                        input.value.length
                    );


                    return;

                }


                if (
                    event.key
                    ===
                    "ArrowDown"
                ) {

                    event.preventDefault();


                    commandHistoryIndex =
                        Math.min(
                            commandHistory.length,
                            commandHistoryIndex
                            +
                            1
                        );


                    input.value =
                        commandHistory[
                            commandHistoryIndex
                        ]
                        ||
                        "";


                    input.setSelectionRange(
                        input.value.length,
                        input.value.length
                    );

                }


                if (
                    event.ctrlKey
                    &&
                    event.key
                        .toLowerCase()
                        ===
                        "l"
                ) {

                    event.preventDefault();


                    historyElement.innerHTML =
                        "";


                    simulationState
                        .clearTerminalHistory();

                }

            }
        );


        screen.addEventListener(
            "click",
            () => {

                input.focus();

            }
        );

        app.addEventListener(
            "click",
            event => {

                if (
                    !event.target.closest(
                        "button"
                    )
                ) {

                    input.focus();

                }

            }
        );


        window.addEventListener(
            "careergrid:filesystem-changed",
            updatePrompt
        );


        // =========================================
        // INITIALIZE
        // =========================================

        restoreHistory();

        updatePrompt();

        window.setTimeout(
            () => {

                input.focus();

            },
            100
        );
    }
);
