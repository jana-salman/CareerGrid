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

        function createAdvisorResponse(
            userMessage
        ) {

            const lower =
                userMessage.toLowerCase();


            const askingForHelp =
                [
                    "help",
                    "stuck",
                    "clarify",
                    "clarification",
                    "not sure",
                    "where should",
                    "where do i",
                    "guidance"
                ]
                    .some(
                        keyword =>
                            lower.includes(
                                keyword
                            )
                    );


            if (askingForHelp) {

                return (
`Take a closer look at the checkout request itself and compare the data being sent with what the endpoint expects.

I wouldn't change anything yet. First identify exactly where the request and expected payload stop matching.

Let me know what you find.`
                );

            }


            const looksLikeFinalUpdate =
                lower.includes(
                    "branch"
                )
                &&
                (
                    lower.includes(
                        "github"
                    )
                    ||
                    lower.includes(
                        "pull request"
                    )
                    ||
                    lower.includes(
                        "pr"
                    )
                );


            if (looksLikeFinalUpdate) {

                return (
`Thanks for the update. I received your summary and branch information.

I'll review the implementation and testing details and get back to you with feedback.`
                );

            }


            return (
`Thanks for the update.

Keep me posted as you investigate, and reply here if you run into anything blocking you.`
            );

        }


        // =========================================
        // SEND REPLY
        // =========================================

        function sendReply() {

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


            const advisorResponse =
                createAdvisorResponse(
                    body
                );


            window.setTimeout(
                () => {

                    message.thread.push(
                        {
                            id:
                                `advisor-${Date.now()}`,

                            from:
                                message.sender,

                            role:
                                message.senderRole
                                ||
                                "Advisor",

                            type:
                                "advisor",

                            sentAt:
                                new Date()
                                    .toISOString(),

                            body:
                                advisorResponse
                        }
                    );


                    message.unread =
                        true;


                    saveState();

                    updateCounters();

                    renderThread(
                        message
                    );


                    showToast(
                        `${message.sender} replied`
                    );

                },
                1100
            );

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

    }
);