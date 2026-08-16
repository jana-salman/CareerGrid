document.addEventListener(
    "DOMContentLoaded",
    () => {

        const app =
            document.getElementById(
                "mail-app"
            );

        if (!app) {
            return;
        }


        // =========================================
        // WORKSPACE INFORMATION
        // =========================================

        const userName =
            app.dataset.userName || "User";

        const positionId =
            app.dataset.positionId || "";

        const positionTitle =
            app.dataset.positionTitle || "Employee";

        const companyName =
            app.dataset.companyName || "CareerGrid";

        const workspaceKey =
            app.dataset.workspaceKey || "default";


        const storageKey =
            `careergrid-mail-${workspaceKey}`;

        const simulationState =
            window.CareerGridSimulationState;


        // =========================================
        // ELEMENTS
        // =========================================

        const messageList =
            document.getElementById(
                "mail-message-list"
            );

        const searchInput =
            document.getElementById(
                "mail-search"
            );

        const folderButtons =
            document.querySelectorAll(
                "[data-mail-folder]"
            );

        const folderTitle =
            document.getElementById(
                "mail-folder-title"
            );

        const folderSubtitle =
            document.getElementById(
                "mail-folder-subtitle"
            );

        const inboxCount =
            document.getElementById(
                "mail-inbox-count"
            );

        const sentCount =
            document.getElementById(
                "mail-sent-count"
            );

        const unreadBadge =
            document.getElementById(
                "mail-unread-badge"
            );

        const emptyState =
            document.getElementById(
                "mail-empty-state"
            );
        
        const readingPane =
            document.getElementById(
                "mail-reading-pane"
            );

        const messageView =
            document.getElementById(
                "mail-message-view"
            );

        const messageSubject =
            document.getElementById(
                "mail-message-subject"
            );

        const messagePriority =
            document.getElementById(
                "mail-message-priority"
            );

        const messageDeadline =
            document.getElementById(
                "mail-message-deadline"
            );

        const taskStatus =
            document.getElementById(
                "mail-task-status"
            );

        const threadElement =
            document.getElementById(
                "mail-thread"
            );

        const attachmentsSection =
            document.getElementById(
                "mail-attachments"
            );

        const attachmentsList =
            document.getElementById(
                "mail-attachment-list"
            );

        const replyButton =
            document.getElementById(
                "mail-reply-button"
            );

        const composer =
            document.getElementById(
                "mail-composer"
            );

        const composeRecipient =
            document.getElementById(
                "mail-compose-recipient"
            );

        const replyText =
            document.getElementById(
                "mail-reply-text"
            );

        const sendButton =
            document.getElementById(
                "mail-send-button"
            );

        const cancelButton =
            document.getElementById(
                "mail-cancel-reply"
            );

        const toast =
            document.getElementById(
                "mail-toast"
            );


        // =========================================
        // DATE HELPERS
        // =========================================

        function createInitialDeadline() {

            const now = new Date();

            const deadline =
                new Date(
                    now.getTime()
                    + (4 * 60 * 60 * 1000)
                );

            deadline.setMinutes(
                0,
                0,
                0
            );

            return deadline.toISOString();

        }


        function formatTime(value) {

            const date = new Date(value);

            return date.toLocaleTimeString(
                [],
                {
                    hour: "numeric",
                    minute: "2-digit"
                }
            );

        }


        function formatDeadline(value) {

            const date = new Date(value);

            const today =
                new Date();

            const sameDay =
                date.toDateString()
                ===
                today.toDateString();


            if (sameDay) {

                return (
                    "Due today at "
                    +
                    date.toLocaleTimeString(
                        [],
                        {
                            hour: "numeric",
                            minute: "2-digit"
                        }
                    )
                );

            }


            return (
                "Due "
                +
                date.toLocaleDateString(
                    [],
                    {
                        month: "short",
                        day: "numeric"
                    }
                )
                +
                " at "
                +
                date.toLocaleTimeString(
                    [],
                    {
                        hour: "numeric",
                        minute: "2-digit"
                    }
                )
            );

        }


        // =========================================
        // INITIAL EMAIL DATA
        // =========================================

        function buildInitialState() {

            const now =
                Date.now();

            const deadline =
                createInitialDeadline();


            const advisorName =
                "Avery Patel";


            return {

                activeFolder:
                    "inbox",

                selectedMessageId:
                    null,

                downloadedAttachments:
                    [],

                inbox: [

                    {
                        id:
                            "task-checkout",

                        sender:
                            advisorName,

                        senderRole:
                            "Senior Engineer",

                        subject:
                            "Checkout API failing after latest update",

                        preview:
                            "Can you investigate the checkout failure and push a fix?",

                        receivedAt:
                            new Date(
                                now - (8 * 60 * 1000)
                            ).toISOString(),

                        unread:
                            true,

                        priority:
                            "high",

                        deadline:
                            deadline,

                        task:
                            true,

                        attachments: [

                            {
                                id:
                                    "checkout-project",

                                name:
                                    "checkout-service.zip",

                                size:
                                    "18 KB",

                                type:
                                    "ZIP"
                            },

                            {
                                id:
                                    "checkout-logs",

                                name:
                                    "checkout-error.log",

                                size:
                                    "4 KB",

                                type:
                                    "LOG"
                            }

                        ],

                        thread: [

                            {
                                id:
                                    "task-checkout-original",

                                from:
                                    advisorName,

                                role:
                                    "Senior Engineer",

                                type:
                                    "advisor",

                                sentAt:
                                    new Date(
                                        now - (8 * 60 * 1000)
                                    ).toISOString(),

                                body:
`Hi ${userName},

We're seeing checkout requests fail for some users after the latest update.

I've attached the relevant checkout service files and an error log from the failed requests.

Please investigate the issue, make the necessary fix in a separate branch, and test the checkout flow.

Once you're done, reply to this thread with:

• what caused the issue
• what you changed
• how you tested it
• your branch name
• your GitHub or pull request link

If you're blocked or need clarification, reply here and I'll help point you in the right direction.

Thanks,
${advisorName}`
                            }

                        ]
                    },


                    {
                        id:
                            "standup",

                        sender:
                            "Engineering Team",

                        senderRole:
                            "Team",

                        subject:
                            "Stand-up notes — today's priorities",

                        preview:
                            "A few updates and blockers from this morning's stand-up.",

                        receivedAt:
                            new Date(
                                now - (45 * 60 * 1000)
                            ).toISOString(),

                        unread:
                            true,

                        priority:
                            "normal",

                        deadline:
                            null,

                        task:
                            false,

                        attachments:
                            [],

                        thread: [

                            {
                                id:
                                    "standup-original",

                                from:
                                    "Engineering Team",

                                role:
                                    companyName,

                                type:
                                    "advisor",

                                sentAt:
                                    new Date(
                                        now - (45 * 60 * 1000)
                                    ).toISOString(),

                                body:
`Good morning team,

Today's priorities are checkout stability, monitoring the latest release, and reviewing any open pull requests before the end of the day.

Please post blockers in the appropriate project thread.

Have a good day.`
                            }

                        ]
                    },


                    {
                        id:
                            "security",

                        sender:
                            "IT Operations",

                        senderRole:
                            "IT",

                        subject:
                            "Developer environment reminder",

                        preview:
                            "Please keep project credentials outside source control.",

                        receivedAt:
                            new Date(
                                now - (92 * 60 * 1000)
                            ).toISOString(),

                        unread:
                            false,

                        priority:
                            "normal",

                        deadline:
                            null,

                        task:
                            false,

                        attachments:
                            [],

                        thread: [

                            {
                                id:
                                    "security-original",

                                from:
                                    "IT Operations",

                                role:
                                    companyName,

                                type:
                                    "advisor",

                                sentAt:
                                    new Date(
                                        now - (92 * 60 * 1000)
                                    ).toISOString(),

                                body:
`Hi ${userName},

Quick reminder to keep credentials, API keys, and local environment files out of source control.

Use the project's environment configuration and ignore rules when working with repositories.

Thanks,
IT Operations`
                            }

                        ]
                    },


                    {
                        id:
                            "welcome",

                        sender:
                            "People Team",

                        senderRole:
                            "People Operations",

                        subject:
                            `Welcome to ${companyName}`,

                        preview:
                            `Welcome to your ${positionTitle} workspace.`,

                        receivedAt:
                            new Date(
                                now - (3 * 60 * 60 * 1000)
                            ).toISOString(),

                        unread:
                            false,

                        priority:
                            "normal",

                        deadline:
                            null,

                        task:
                            false,

                        attachments:
                            [],

                        thread: [

                            {
                                id:
                                    "welcome-original",

                                from:
                                    "People Team",

                                role:
                                    "People Operations",

                                type:
                                    "advisor",

                                sentAt:
                                    new Date(
                                        now - (3 * 60 * 60 * 1000)
                                    ).toISOString(),

                                body:
`Welcome, ${userName}!

We're glad to have you joining the ${companyName} team as a ${positionTitle}.

Your project assignments and communication will appear in this workspace.

Good luck with your first day!`
                            }

                        ]
                    }

                ],

                sent:
                    []

            };

        }


        // =========================================
        // STATE
        // =========================================

        function loadState() {

            try {

                const stored =
                    localStorage.getItem(
                        storageKey
                    );

                if (stored) {

                    return JSON.parse(
                        stored
                    );

                }

            }
            catch (error) {

                console.warn(
                    "Unable to load mail state:",
                    error
                );

            }


            const initial =
                buildInitialState();

            saveState(
                initial
            );

            return initial;

        }


        function saveState(
            value = state
        ) {

            localStorage.setItem(
                storageKey,
                JSON.stringify(value)
            );

        }


        let state =
            loadState();



        // =========================================
        // LEGACY MAIL DOWNLOAD MIGRATION
        // =========================================

        if (
            simulationState
            &&
            Array.isArray(
                state.downloadedAttachments
            )
        ) {

            state.downloadedAttachments
                .forEach(
                    attachmentId => {

                        if (
                            !simulationState
                                .hasDownloadedAttachment(
                                    attachmentId
                                )
                        ) {

                            simulationState
                                .saveAttachmentById(
                                    attachmentId
                                );

                        }

                    }
                );

        }
        // =========================================
        // UTILITIES
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
                    2400
                );

        }


        function getFolderMessages() {

            return (
                state.activeFolder
                === "sent"
            )
                ? state.sent
                : state.inbox;

        }


        function getSelectedMessage() {

            const allMessages =
                [
                    ...state.inbox,
                    ...state.sent
                ];


            return allMessages.find(
                message =>
                    message.id
                    ===
                    state.selectedMessageId
            );

        }


        function escapeHtml(
            value = ""
        ) {

            return value
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


        // =========================================
        // COUNTERS
        // =========================================

        function updateCounters() {

            const unread =
                state.inbox.filter(
                    message =>
                        message.unread
                ).length;


            inboxCount.textContent =
                unread;

            sentCount.textContent =
                state.sent.length;


            unreadBadge.textContent =
                unread;


            unreadBadge.style.display =
                unread > 0
                    ? "grid"
                    : "none";

        }


        // =========================================
        // MESSAGE LIST
        // =========================================

        function renderMessageList() {

            const messages =
                getFolderMessages();


            const query =
                searchInput.value
                    .trim()
                    .toLowerCase();


            const filtered =
                messages.filter(
                    message => {

                        if (!query) {
                            return true;
                        }

                        const haystack =
                            [
                                message.sender,
                                message.subject,
                                message.preview
                            ]
                                .join(" ")
                                .toLowerCase();


                        return haystack.includes(
                            query
                        );

                    }
                );


            messageList.innerHTML =
                "";


            if (
                filtered.length
                === 0
            ) {

                messageList.innerHTML =
                    `
                    <div class="mail-empty-state">
                        <p>
                            No messages found.
                        </p>
                    </div>
                    `;

                return;
            }


            filtered.forEach(
                message => {

                    const button =
                        document.createElement(
                            "button"
                        );


                    button.type =
                        "button";


                    button.className =
                        "mail-list-item";


                    if (
                        message.unread
                        &&
                        state.activeFolder
                        === "inbox"
                    ) {

                        button.classList.add(
                            "is-unread"
                        );

                    }


                    if (
                        message.id
                        ===
                        state.selectedMessageId
                    ) {

                        button.classList.add(
                            "is-selected"
                        );

                    }


                    const deadlineHtml =
                        message.deadline
                            ?
                            `
                            <div class="mail-list-deadline">
                                ${escapeHtml(
                                    formatDeadline(
                                        message.deadline
                                    )
                                )}
                            </div>
                            `
                            :
                            "";


                    button.innerHTML =
                        `
                        <div class="mail-list-topline">

                            <span class="mail-list-sender">
                                ${escapeHtml(
                                    message.sender
                                )}
                            </span>

                            <span class="mail-list-time">
                                ${escapeHtml(
                                    formatTime(
                                        message.receivedAt
                                    )
                                )}
                            </span>

                        </div>

                        <div class="mail-list-subject">
                            ${escapeHtml(
                                message.subject
                            )}
                        </div>

                        <div class="mail-list-preview">
                            ${escapeHtml(
                                message.preview
                            )}
                        </div>

                        ${deadlineHtml}
                        `;


                    button.addEventListener(
                        "click",
                        () => {

                            selectMessage(
                                message.id
                            );

                        }
                    );


                    messageList.appendChild(
                        button
                    );

                }
            );

        }


        // =========================================
        // SELECT MESSAGE
        // =========================================

        function selectMessage(
            messageId
        ) {

            state.selectedMessageId =
                messageId;


            const inboxMessage =
                state.inbox.find(
                    message =>
                        message.id
                        ===
                        messageId
                );


            if (inboxMessage) {

                inboxMessage.unread =
                    false;

            }


            saveState();

            updateCounters();

            renderMessageList();

            renderSelectedMessage();


            // Always open the selected email from the top
            // instead of keeping the previous scroll position.
            requestAnimationFrame(
                () => {

                    if (readingPane) {

                        readingPane.scrollTop = 0;

                    }

                }
            );

        }


        // =========================================
        // THREAD
        // =========================================

        function renderThread(
            message
        ) {

            threadElement.innerHTML =
                "";


            message.thread.forEach(
                threadMessage => {

                    const card =
                        document.createElement(
                            "article"
                        );


                    card.className =
                        "mail-thread-message";


                    if (
                        threadMessage.type
                        === "user"
                    ) {

                        card.classList.add(
                            "is-user"
                        );

                    }


                    const initial =
                        (
                            threadMessage.from
                            ||
                            "U"
                        )[0]
                            .toUpperCase();


                    card.innerHTML =
                        `
                        <header class="mail-thread-message-header">

                            <div class="mail-sender-block">

                                <span class="mail-sender-avatar">
                                    ${escapeHtml(
                                        initial
                                    )}
                                </span>

                                <div>

                                    <strong>
                                        ${escapeHtml(
                                            threadMessage.from
                                        )}
                                    </strong>

                                    <small>
                                        ${escapeHtml(
                                            threadMessage.role
                                            || ""
                                        )}
                                    </small>

                                </div>

                            </div>

                            <span class="mail-thread-time">
                                ${escapeHtml(
                                    formatTime(
                                        threadMessage.sentAt
                                    )
                                )}
                            </span>

                        </header>

                        <div class="mail-thread-body">
                            ${escapeHtml(
                                threadMessage.body
                            )}
                        </div>
                        `;

                    if (threadMessage.attachments?.length) {
                        threadMessage.attachments.forEach(attachment => {
                            const button = document.createElement("button");
                            button.type = "button";
                            button.className = "mail-download-button";
                            button.textContent = attachment.name;
                            button.addEventListener("click", () => {
                                const evaluation = simulationState.getEvaluation(attachment.threadId);
                                window.CareerGridReport?.open(evaluation, attachment.meta || {});
                            });
                            card.appendChild(button);
                        });
                    }


                    threadElement.appendChild(
                        card
                    );

                }
            );

        }


        // =========================================
        // ATTACHMENTS
        // =========================================

        function renderAttachments(
            message
        ) {

            attachmentsList.innerHTML =
                "";


            if (
                !message.attachments
                ||
                message.attachments.length
                === 0
            ) {

                attachmentsSection.hidden =
                    true;

                return;
            }


            attachmentsSection.hidden =
                false;


            message.attachments.forEach(
                attachment => {

                    const isEvaluationReport =
                        attachment.type === "evaluation-report";

                    const downloaded =
                        simulationState
                            ?
                            simulationState
                                .hasDownloadedAttachment(
                                    attachment.id
                                )
                            :
                            state.downloadedAttachments
                                .includes(
                                    attachment.id
                                );


                    const card =
                        document.createElement(
                            "article"
                        );


                    card.className =
                        "mail-attachment-card";


                    card.innerHTML =
                        `
                        <span class="mail-attachment-icon">
                            ${escapeHtml(
                                attachment.type
                            )}
                        </span>

                        <div class="mail-attachment-info">

                            <strong>
                                ${escapeHtml(
                                    attachment.name
                                )}
                            </strong>

                            <span>
                                ${escapeHtml(
                                    attachment.size
                                )}
                            </span>

                        </div>

                        <button
                            type="button"
                            class="
                                mail-download-button
                                ${
                                    downloaded
                                        ? "is-downloaded"
                                        : ""
                                }
                            "
                        >
                            ${
                                downloaded
                                    ? "Saved"
                                    : "Download"
                            }
                        </button>
                        `;


                    const downloadButton =
                        card.querySelector(
                            ".mail-download-button"
                        );


                    downloadButton.addEventListener(
                        "click",
                        () => {

                            if (isEvaluationReport) {

                                const evaluation =
                                    simulationState.getEvaluation(
                                        attachment.threadId
                                    );

                                window.CareerGridReport?.open(
                                    evaluation,
                                    attachment.meta
                                    ||
                                    {}
                                );

                                return;

                            }

                            downloadAttachment(
                                attachment
                            );

                        }
                    );


                    attachmentsList.appendChild(
                        card
                    );

                }
            );

        }


        function downloadAttachment(
            attachment
        ) {

            if (simulationState) {

                simulationState
                    .saveAttachmentById(
                        attachment.id
                    );

            }


            // Keep this temporarily for compatibility
            // with Mail's existing local state.
            if (
                !state.downloadedAttachments
                    .includes(
                        attachment.id
                    )
            ) {

                state.downloadedAttachments.push(
                    attachment.id
                );

                saveState();

            }


            showToast(
                `${attachment.name} saved to Downloads`
            );


            const selected =
                getSelectedMessage();


            if (selected) {

                renderAttachments(
                    selected
                );

            }

        }


        // =========================================
        // MESSAGE VIEW
        // =========================================

        function renderSelectedMessage() {

            const message =
                getSelectedMessage();


            if (!message) {

                emptyState.hidden =
                    false;

                messageView.hidden =
                    true;

                return;
            }


            emptyState.hidden =
                true;

            messageView.hidden =
                false;


            messageSubject.textContent =
                message.subject;


            messagePriority.className =
                "mail-priority";


            if (
                message.priority
                === "high"
            ) {

                messagePriority.classList.add(
                    "priority-high"
                );

                messagePriority.textContent =
                    "HIGH PRIORITY";

            }
            else {

                messagePriority.classList.add(
                    "priority-normal"
                );

                messagePriority.textContent =
                    "NORMAL";

            }


            if (message.deadline) {

                messageDeadline.hidden =
                    false;

                messageDeadline.textContent =
                    formatDeadline(
                        message.deadline
                    );

            }
            else {

                messageDeadline.hidden =
                    true;

            }


            if (
                message.task
                &&
                simulationState
            ) {

                const status =
                    simulationState.getSubmissionStatus(
                        message.id
                    );

                taskStatus.hidden = false;
                taskStatus.textContent =
                    status === "submitted"
                        ? "Task status: Submitted"
                        : "Task status: In progress";

            }
            else {

                taskStatus.hidden = true;

            }


            renderThread(
                message
            );


            renderAttachments(
                message
            );


            composeRecipient.textContent =
                message.sender;


            composer.hidden =
                true;


            replyButton.hidden =
                (
                    state.activeFolder
                    === "sent"
                );

        }


        // =========================================
        // FOLDERS
        // =========================================

        function switchFolder(
            folder
        ) {

            state.activeFolder =
                folder;

            state.selectedMessageId =
                null;


            saveState();


            folderButtons.forEach(
                button => {

                    button.classList.toggle(
                        "is-active",
                        button.dataset.mailFolder
                        ===
                        folder
                    );

                }
            );


            if (
                folder
                === "sent"
            ) {

                folderTitle.textContent =
                    "Sent";

                folderSubtitle.textContent =
                    "Messages you've sent";

            }
            else {

                folderTitle.textContent =
                    "Inbox";

                folderSubtitle.textContent =
                    "Your workplace messages";

            }


            searchInput.value =
                "";


            renderMessageList();

            renderSelectedMessage();

            if (readingPane) {

                readingPane.scrollTop = 0;

            }

        }


        // =========================================
        // COMPOSER
        // =========================================

        function openComposer() {

            const message =
                getSelectedMessage();


            if (!message) {
                return;
            }


            composer.hidden =
                false;


            replyText.value =
                "";


            replyText.focus();

        }


        function closeComposer() {

            composer.hidden =
                true;

            replyText.value =
                "";

        }


        // =========================================
        // ADVISOR RESPONSE
        // =========================================

        function assessSubmission(
            message,
            body
        ) {

            const submission =
                simulationState?.getSubmission(
                    message.id
                );

            const urls =
                [
                    ...body.matchAll(
                        /https:\/\/github\.com\/careergrid-sim\/[^\s/]+\/pull\/\d+/gi
                    )
                ]
                    .map(
                        match => match[0]
                    );

            const branchMatch =
                body.match(
                    /(?:^|\n)\s*branch\s*:\s*([A-Za-z0-9._/-]+)/i
                );

            const reportedBranch =
                branchMatch?.[1]
                ||
                "";

            const repositories =
                simulationState
                    ?
                    simulationState.getRepositories()
                    :
                    {};

            let validated = null;

            Object.values(repositories)
                .some(
                    repository =>
                        simulationState.getPullRequests(
                            repository.rootPath
                        )
                            .some(
                                pullRequest => {

                                    if (
                                        urls.includes(
                                            pullRequest.url
                                        )
                                    ) {

                                        validated = {
                                            repository,
                                            pullRequest
                                        };

                                        return true;

                                    }

                                    return false;

                                }
                            )
                );

            const lower =
                body.toLowerCase();

            const looksLikeSubmission =
                urls.length > 0
                ||
                (
                    Boolean(reportedBranch)
                    &&
                    /pull request|github|\bpr\b|pushed/.test(lower)
                );

            const hasSummary =
                /found|identified|changed|updated|fixed|implemented|investigated|resolved/.test(lower)
                &&
                body.replace(/https?:\/\/\S+/g, "").trim().split(/\s+/).length >= 8;

            const hasVerification =
                /test|tested|testing|verify|verified|validation|reviewed|checked/.test(lower);

            const errors = [];

            if (looksLikeSubmission && !urls.length) {

                errors.push("missing_pull_request");

            }

            if (urls.length && !validated) {

                errors.push("invalid_pull_request");

            }

            if (validated) {

                const { repository, pullRequest } = validated;
                const branch = repository.branches[pullRequest.compareBranch];
                const baseIds = new Set(
                    repository.branches[pullRequest.baseBranch]?.commits.map(commit => commit.id)
                );
                const hasNewCommits = branch?.commits.some(
                    commit => !baseIds.has(commit.id)
                );

                if (pullRequest.status !== "open") errors.push("pull_request_not_open");
                if (!branch) errors.push("missing_compare_branch");
                if (!repository.remote.pushedBranches.includes(pullRequest.compareBranch)) errors.push("branch_not_pushed");
                if (!hasNewCommits) errors.push("no_compare_commits");
                if (reportedBranch && reportedBranch !== pullRequest.compareBranch) errors.push("branch_mismatch");
                if (!hasSummary) errors.push("missing_summary");
                if (!hasVerification) errors.push("missing_verification");
            }

            const complete =
                looksLikeSubmission
                &&
                Boolean(validated)
                &&
                errors.length === 0;

            return {
                submission,
                urls,
                reportedBranch,
                validated,
                looksLikeSubmission,
                hasSummary,
                hasVerification,
                errors,
                complete
            };

        }


        function buildAdvisorContext(
            message,
            body,
            assessment
        ) {

            const repositories =
                simulationState
                    ? simulationState.getRepositories()
                    : {};

            return {
                task: {
                    id: message.id,
                    status: assessment.submission ? "submitted" : "in_progress",
                    title: message.subject,
                    deadline: message.deadline,
                    original_email: message.thread[0]?.body || ""
                },
                advisor: {
                    name: message.sender,
                    role: message.senderRole || "Advisor"
                },
                workspace: { position: positionTitle, company: companyName },
                conversation: message.thread.slice(-12).map(entry => ({
                    from: entry.from,
                    role: entry.role,
                    type: entry.type,
                    body: entry.body,
                    sent_at: entry.sentAt
                })),
                user_message: body,
                repository_context: Object.values(repositories).map(repository => ({
                    path: repository.rootPath,
                    current_branch: repository.currentBranch,
                    branches: Object.keys(repository.branches),
                    pushed_branches: repository.remote.pushedBranches,
                    commits: Object.fromEntries(Object.entries(repository.branches).map(([name, branch]) => [name, branch.commits.map(commit => ({ id: commit.id, message: commit.message, author: commit.author }))]))
                })),
                pull_request_context: assessment.validated ? {
                    detected_url: assessment.validated.pullRequest.url,
                    exists: true,
                    id: assessment.validated.pullRequest.id,
                    repository: assessment.validated.repository.rootPath,
                    base_branch: assessment.validated.pullRequest.baseBranch,
                    compare_branch: assessment.validated.pullRequest.compareBranch,
                    status: assessment.validated.pullRequest.status,
                    is_pushed: assessment.validated.repository.remote.pushedBranches.includes(assessment.validated.pullRequest.compareBranch)
                } : { detected_url: assessment.urls[0] || "", exists: false },
                submission_context: {
                    already_submitted: Boolean(assessment.submission),
                    looks_like_submission: assessment.looksLikeSubmission,
                    validation_errors: assessment.errors,
                    missing_information: assessment.errors.filter(error => error.startsWith("missing_")),
                    guidance_level: Math.min(3, 1 + message.thread.filter(entry => entry.type === "user" && /help|stuck|clarify|not sure/i.test(entry.body)).length)
                }
            };

        }


        function fallbackAdvisorResponse(
            assessment
        ) {

            if (assessment.errors.includes("invalid_pull_request")) return "I couldn't find that pull request in the current project. Please double-check the link and send it again.";
            if (assessment.errors.includes("branch_mismatch")) return "I found the pull request, but the branch name in your update does not match the branch attached to it. Could you confirm the correct branch?";
            if (assessment.errors.includes("missing_pull_request")) return "Thanks for the update. Please send the pull request link once the branch is pushed and ready for review.";
            if (assessment.errors.includes("missing_summary") || assessment.errors.includes("missing_verification")) return "Thanks. Before I review the pull request, please include a brief summary of what you changed and how you verified it.";
            return "Thanks for the update. I’ll review the context and follow up shortly.";

        }


        async function requestAdvisorResponse(
            advisorContext,
            assessment
        ) {

            try {

                const response = await fetch(
                    "/api/simulation/advisor/reply",
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ advisor_context: advisorContext })
                    }
                );

                if (!response.ok) throw new Error("Advisor request failed.");

                const payload = await response.json();

                if (!payload.advisor_reply) throw new Error("Advisor reply missing.");

                return payload.advisor_reply;

            }
            catch (error) {

                console.warn("Advisor AI unavailable:", error);
                return fallbackAdvisorResponse(assessment);

            }

        }

        async function runSubmissionEvaluation(message, assessment) {
            if (!message.task || !assessment.submission || !assessment.validated) return;
            const existing = simulationState.getEvaluation(message.id);
            const pendingAge = existing?.startedAt ? Date.now() - new Date(existing.startedAt).getTime() : 0;
            if (existing?.status === "completed" || (existing?.status === "pending" && pendingAge < 10 * 60 * 1000)) return;
            simulationState.markEvaluationPending(message.id);
            const repository = assessment.validated.repository;
            const pullRequest = assessment.validated.pullRequest;
            const base = repository.branches[pullRequest.baseBranch];
            const compare = repository.branches[pullRequest.compareBranch];
            const before = base?.headSnapshot || {};
            const after = compare?.headSnapshot || {};
            const changedFiles = Object.keys(after).filter(path => !before[path] || before[path].content !== after[path].content).map(path => ({ path, before: before[path]?.content || "", after: after[path]?.content || "" }));
            try {
                const response = await fetch("/api/simulation/evaluation", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ evidence: { task: { title: message.subject, original_email: message.thread[0]?.body, deadline: message.deadline }, submission: assessment.submission, pull_request: pullRequest, repository: { path: repository.rootPath, commits: compare?.commits || [], pushed_branches: repository.remote.pushedBranches }, changed_files: changedFiles, conversation: message.thread } }) });
                if (!response.ok) throw new Error("Evaluation failed");
                const evaluation = await response.json();
                simulationState.recordEvaluation(message.id, evaluation);
                if (!message.thread.some(entry => entry.type === "evaluation-review")) {
                    message.thread.push({ id: `review-${Date.now()}`, from: message.sender, role: message.senderRole || "Advisor", type: "evaluation-review", sentAt: new Date().toISOString(), body: evaluation.review_message || "I've completed my review and attached the feedback report.", attachments: [{ id: `report-${message.id}`, name: "Task Review Report.pdf", type: "evaluation-report", size: "Generated review", threadId: message.id, meta: { task: message.subject, position: positionTitle, company: companyName } }] });
                    saveState(); renderThread(message);
                }
            } catch (error) { simulationState.markEvaluationFailed(message.id, error.message); }
        }

        function ensureReviewMessage(message, evaluation) {
            if (message.thread.some(entry => entry.type === "evaluation-review")) return;
            message.thread.push({ id: `review-${message.id}`, from: message.sender, role: message.senderRole || "Advisor", type: "evaluation-review", sentAt: evaluation.completedAt || new Date().toISOString(), body: evaluation.data?.review_message || "I've completed my review and attached the feedback report.", attachments: [{ id: `report-${message.id}`, name: "Task Review Report.pdf", type: "evaluation-report", size: "Generated review", threadId: message.id, meta: { task: message.subject, position: positionTitle, company: companyName } }] });
            saveState();
        }

        function recoverSubmittedEvaluations() {
            if (!simulationState) return;
            state.inbox.filter(message => message.task).forEach(message => {
                const submission = simulationState.getSubmission(message.id);
                if (submission?.status !== "submitted") return;
                const evaluation = simulationState.getEvaluation(message.id);
                if (evaluation?.status === "completed") { ensureReviewMessage(message, evaluation); return; }
                const assessment = assessSubmission(message, submission.rawMessage || "");
                assessment.submission = submission;
                runSubmissionEvaluation(message, assessment);
            });
        }


        // =========================================
        // SEND REPLY
        // =========================================

        async function sendReply() {

            const message =
                getSelectedMessage();


            if (!message) {
                return;
            }


            const body =
                replyText.value.trim();


            if (!body) {

                showToast(
                    "Write a message before sending."
                );

                return;
            }


            const assessment =
                assessSubmission(
                    message,
                    body
                );


            const now =
                new Date().toISOString();


            const userThreadMessage =
                {
                    id:
                        `user-${Date.now()}`,

                    from:
                        userName,

                    role:
                        positionTitle,

                    type:
                        "user",

                    sentAt:
                        now,

                    body:
                        body
                };


            message.thread.push(
                userThreadMessage
            );


            if (
                message.task
                &&
                assessment.complete
                &&
                !assessment.submission
            ) {

                const recordResult =
                    simulationState.recordSubmission(
                    {
                        messageId: userThreadMessage.id,
                        threadId: message.id,
                        rawMessage: body,
                        repositoryPath: assessment.validated.repository.rootPath,
                        branch: assessment.validated.pullRequest.compareBranch,
                        pullRequestId: assessment.validated.pullRequest.id,
                        pullRequestUrl: assessment.validated.pullRequest.url,
                        extracted: {
                            hasSummary: assessment.hasSummary,
                            hasVerification: assessment.hasVerification
                        }
                    }
                );

                if (recordResult.success) {

                    assessment.submission =
                        recordResult.submission;

                }

            }


            state.sent.unshift(
                {
                    id:
                        `sent-${Date.now()}`,

                    sender:
                        `To: ${message.sender}`,

                    senderRole:
                        message.senderRole,

                    subject:
                        `Re: ${message.subject}`,

                    preview:
                        body,

                    receivedAt:
                        now,

                    unread:
                        false,

                    priority:
                        "normal",

                    deadline:
                        null,

                    task:
                        false,

                    attachments:
                        [],

                    thread:
                        [
                            userThreadMessage
                        ]
                }
            );


            saveState();


            closeComposer();

            renderThread(
                message
            );

            updateCounters();


            showToast(
                "Message sent."
            );


            const advisorContext =
                buildAdvisorContext(
                    message,
                    body,
                    assessment
                );

            sendButton.disabled = true;

            const advisorResponse =
                await requestAdvisorResponse(
                    advisorContext,
                    assessment
                );

            sendButton.disabled = false;

            message.thread.push(
                {
                    id: `advisor-${Date.now()}`,
                    from: message.sender,
                    role: message.senderRole || "Advisor",
                    type: "advisor",
                    sentAt: new Date().toISOString(),
                    body: advisorResponse
                }
            );

            message.unread = true;

            saveState();
            updateCounters();
            renderThread(message);
            renderSelectedMessage();
            showToast(`${message.sender} replied`);

            await runSubmissionEvaluation(message, assessment);

        }


        // =========================================
        // EVENTS
        // =========================================

        folderButtons.forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        switchFolder(
                            button.dataset.mailFolder
                        );

                    }
                );

            }
        );


        searchInput.addEventListener(
            "input",
            renderMessageList
        );


        replyButton.addEventListener(
            "click",
            openComposer
        );


        cancelButton.addEventListener(
            "click",
            closeComposer
        );


        sendButton.addEventListener(
            "click",
            sendReply
        );


        window.addEventListener(
            "careergrid:filesystem-changed",
            () => {

                if (getSelectedMessage()) {

                    renderSelectedMessage();

                }

            }
        );


        // Ctrl + Enter to send

        replyText.addEventListener(
            "keydown",
            event => {

                if (
                    event.ctrlKey
                    &&
                    event.key
                        === "Enter"
                ) {

                    sendReply();

                }

            }
        );


        // =========================================
        // INITIAL RENDER
        // =========================================

        switchFolder(
            state.activeFolder
            ||
            "inbox"
        );

        updateCounters();

        recoverSubmittedEvaluations();

    }
);
