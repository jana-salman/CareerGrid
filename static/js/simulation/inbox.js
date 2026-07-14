(() => {
    "use strict";

    function initializeInboxTask() {
        const form = document.getElementById("inbox-task-form");

        /*
         * Stop safely on simulation steps that do not contain
         * the interactive inbox.
         */
        if (!form) {
            return;
        }

        const inboxDataElement =
            document.getElementById("generated-inbox-data");

        const savedAnswerElement =
            document.getElementById("saved-inbox-answer");

        const hiddenAnswer =
            document.getElementById("answer");

        const replyTextarea =
            document.getElementById("inbox-reply");

        const replyValidationMessage =
            document.getElementById(
                "reply-validation-message"
            );

        const priorityList =
            document.getElementById("priority-list");

        const mailItems = Array.from(
            document.querySelectorAll(".mail-item")
        );

        /*
         * Make sure all required HTML elements exist before
         * continuing.
         */
        if (
            !inboxDataElement ||
            !hiddenAnswer ||
            !replyTextarea ||
            !priorityList
        ) {
            console.error(
                "CareerGrid inbox could not start because required HTML elements are missing."
            );

            return;
        }

        let emails = [];
        let savedResponse = null;
        let draggedItem = null;

        const openedEmailIds = new Set();

        /*
         * Read the public AI-generated email data from the
         * application/json script element.
         */
        try {
            emails = JSON.parse(
                inboxDataElement.textContent.trim()
            );

            if (!Array.isArray(emails)) {
                throw new Error(
                    "Generated inbox data must be an array."
                );
            }
        } catch (error) {
            console.error(
                "Could not read generated inbox data:",
                error
            );

            return;
        }

        /*
         * Restore a response when the user returns to Step 1.
         *
         * saved_answer is normally a JSON string stored inside
         * another JSON value, so it may need to be parsed twice.
         */
        if (savedAnswerElement) {
            try {
                const firstParse = JSON.parse(
                    savedAnswerElement.textContent.trim()
                );

                if (typeof firstParse === "string") {
                    savedResponse = JSON.parse(firstParse);
                } else if (
                    firstParse &&
                    typeof firstParse === "object"
                ) {
                    savedResponse = firstParse;
                }
            } catch (error) {
                savedResponse = null;
            }
        }

        function findEmail(emailId) {
            return emails.find(
                (email) => email.id === emailId
            );
        }

        function setElementText(elementId, value) {
            const element =
                document.getElementById(elementId);

            if (element) {
                element.textContent = value || "";
            }
        }

        function displayEmail(emailId) {
            const email = findEmail(emailId);

            if (!email) {
                return;
            }

            openedEmailIds.add(emailId);

            mailItems.forEach((item) => {
                const isActive =
                    item.dataset.emailId === emailId;

                item.classList.toggle(
                    "active",
                    isActive
                );

                item.setAttribute(
                    "aria-selected",
                    String(isActive)
                );
            });

            setElementText(
                "active-email-subject",
                email.subject
            );

            setElementText(
                "active-email-time",
                email.timestamp
            );

            setElementText(
                "active-email-sender",
                email.sender_name
            );

            setElementText(
                "active-email-role",
                email.sender_role
            );

            setElementText(
                "active-email-body",
                email.body
            );

            setElementText(
                "active-email-avatar",
                email.sender_name
                    ? email.sender_name
                        .charAt(0)
                        .toUpperCase()
                    : "?"
            );

            updateAttachment(email);
            updateLinkedTicket(email);
        }

        function updateAttachment(email) {
            const attachmentContainer =
                document.getElementById(
                    "active-email-attachment"
                );

            const attachmentName =
                document.getElementById(
                    "active-attachment-name"
                );

            if (
                !attachmentContainer ||
                !attachmentName
            ) {
                return;
            }

            if (
                email.has_attachment &&
                email.attachment_name
            ) {
                attachmentContainer.hidden = false;
                attachmentName.textContent =
                    email.attachment_name;
            } else {
                attachmentContainer.hidden = true;
                attachmentName.textContent = "";
            }
        }

        function updateLinkedTicket(email) {
            const ticketContainer =
                document.getElementById(
                    "active-email-ticket"
                );

            const ticketId =
                document.getElementById(
                    "active-ticket-id"
                );

            if (
                !ticketContainer ||
                !ticketId
            ) {
                return;
            }

            if (email.linked_ticket_id) {
                ticketContainer.hidden = false;
                ticketId.textContent =
                    email.linked_ticket_id;
            } else {
                ticketContainer.hidden = true;
                ticketId.textContent = "";
            }
        }

        /*
         * Open an email when its inbox item is clicked.
         */
        mailItems.forEach((item) => {
            item.addEventListener("click", () => {
                displayEmail(
                    item.dataset.emailId
                );
            });
        });

        function getPriorityItems() {
            return Array.from(
                priorityList.querySelectorAll(
                    ".priority-item"
                )
            );
        }

        function updatePriorityRanks() {
            getPriorityItems().forEach(
                (item, index) => {
                    const rank =
                        item.querySelector(
                            ".priority-rank"
                        );

                    if (rank) {
                        rank.textContent =
                            String(index + 1);
                    }

                    const subject =
                        item.querySelector(
                            ".priority-email-information strong"
                        )?.textContent?.trim();

                    const upButton =
                        item.querySelector(
                            ".move-priority-up"
                        );

                    const downButton =
                        item.querySelector(
                            ".move-priority-down"
                        );

                    if (upButton) {
                        upButton.setAttribute(
                            "aria-label",
                            `Move ${subject || "email"} higher`
                        );
                    }

                    if (downButton) {
                        downButton.setAttribute(
                            "aria-label",
                            `Move ${subject || "email"} lower`
                        );
                    }
                }
            );
        }

        function moveItemUp(item) {
            const previousItem =
                item.previousElementSibling;

            if (!previousItem) {
                return;
            }

            priorityList.insertBefore(
                item,
                previousItem
            );

            updatePriorityRanks();
        }

        function moveItemDown(item) {
            const nextItem =
                item.nextElementSibling;

            if (!nextItem) {
                return;
            }

            priorityList.insertBefore(
                nextItem,
                item
            );

            updatePriorityRanks();
        }

        /*
         * Handle the up and down arrow controls.
         */
        priorityList.addEventListener(
            "click",
            (event) => {
                const priorityItem =
                    event.target.closest(
                        ".priority-item"
                    );

                if (!priorityItem) {
                    return;
                }

                if (
                    event.target.closest(
                        ".move-priority-up"
                    )
                ) {
                    moveItemUp(priorityItem);
                    return;
                }

                if (
                    event.target.closest(
                        ".move-priority-down"
                    )
                ) {
                    moveItemDown(priorityItem);
                }
            }
        );

        /*
         * Drag-and-drop prioritization.
         */
        priorityList.addEventListener(
            "dragstart",
            (event) => {
                draggedItem =
                    event.target.closest(
                        ".priority-item"
                    );

                if (!draggedItem) {
                    return;
                }

                draggedItem.classList.add(
                    "dragging"
                );

                if (event.dataTransfer) {
                    event.dataTransfer.effectAllowed =
                        "move";

                    event.dataTransfer.setData(
                        "text/plain",
                        draggedItem.dataset.emailId || ""
                    );
                }
            }
        );

        priorityList.addEventListener(
            "dragover",
            (event) => {
                event.preventDefault();

                if (!draggedItem) {
                    return;
                }

                const targetItem =
                    event.target.closest(
                        ".priority-item"
                    );

                if (
                    !targetItem ||
                    targetItem === draggedItem
                ) {
                    return;
                }

                const targetBox =
                    targetItem.getBoundingClientRect();

                const mouseIsBelowMiddle =
                    event.clientY >
                    targetBox.top +
                    targetBox.height / 2;

                if (mouseIsBelowMiddle) {
                    targetItem.after(draggedItem);
                } else {
                    targetItem.before(draggedItem);
                }
            }
        );

        priorityList.addEventListener(
            "drop",
            (event) => {
                event.preventDefault();
                updatePriorityRanks();
            }
        );

        priorityList.addEventListener(
            "dragend",
            () => {
                if (draggedItem) {
                    draggedItem.classList.remove(
                        "dragging"
                    );
                }

                draggedItem = null;
                updatePriorityRanks();
            }
        );

        function restoreSavedResponse() {
            if (!emails.length) {
                return;
            }

            if (!savedResponse) {
                displayEmail(emails[0].id);
                updatePriorityRanks();

                return;
            }

            if (
                Array.isArray(
                    savedResponse.opened_emails
                )
            ) {
                savedResponse.opened_emails.forEach(
                    (emailId) => {
                        if (findEmail(emailId)) {
                            openedEmailIds.add(
                                emailId
                            );
                        }
                    }
                );
            }

            if (
                Array.isArray(
                    savedResponse.priority_order
                )
            ) {
                savedResponse.priority_order.forEach(
                    (emailId) => {
                        const priorityItem =
                            priorityList.querySelector(
                                `.priority-item[data-email-id="${emailId}"]`
                            );

                        if (priorityItem) {
                            priorityList.appendChild(
                                priorityItem
                            );
                        }
                    }
                );
            }

            const actionOptions = Array.from(
                form.querySelectorAll(
                    'input[name="selected_action"]'
                )
            );

            actionOptions.forEach((option) => {
                option.checked =
                    option.value ===
                    savedResponse.selected_action;
            });

            replyTextarea.value =
                savedResponse.written_reply || "";

            const openedEmails =
                savedResponse.opened_emails;

            let lastOpenedEmailId = null;

            if (
                Array.isArray(openedEmails) &&
                openedEmails.length > 0
            ) {
                lastOpenedEmailId =
                    openedEmails[
                        openedEmails.length - 1
                    ];
            }

            if (!findEmail(lastOpenedEmailId)) {
                lastOpenedEmailId =
                    emails[0].id;
            }

            displayEmail(lastOpenedEmailId);
            updatePriorityRanks();
        }

        /*
         * Remove custom reply errors while the user is typing.
         */
        replyTextarea.addEventListener(
            "input",
            () => {
                replyTextarea.setCustomValidity("");

                if (replyValidationMessage) {
                    replyValidationMessage.hidden =
                        true;
                }
            }
        );

        /*
         * Convert the interactive response into JSON before
         * submitting it to Flask.
         */
        form.addEventListener(
            "submit",
            (event) => {
                const reply =
                    replyTextarea.value.trim();

                if (reply.length < 15) {
                    event.preventDefault();

                    replyTextarea.setCustomValidity(
                        "Please write a meaningful professional reply."
                    );

                    if (replyValidationMessage) {
                        replyValidationMessage.hidden =
                            false;
                    }

                    replyTextarea.reportValidity();
                    replyTextarea.focus();

                    return;
                }

                if (reply.length > 2000) {
                    event.preventDefault();

                    replyTextarea.setCustomValidity(
                        "Your reply must contain no more than 2000 characters."
                    );

                    replyTextarea.reportValidity();
                    replyTextarea.focus();

                    return;
                }

                replyTextarea.setCustomValidity("");

                const selectedAction =
                    form.querySelector(
                        'input[name="selected_action"]:checked'
                    );

                if (!selectedAction) {
                    event.preventDefault();

                    const firstAction =
                        form.querySelector(
                            'input[name="selected_action"]'
                        );

                    if (firstAction) {
                        firstAction.focus();
                    }

                    return;
                }

                const priorityOrder =
                    getPriorityItems().map(
                        (item) =>
                            item.dataset.emailId
                    );

                const responseData = {
                    task_type: "inbox",
                    opened_emails:
                        Array.from(
                            openedEmailIds
                        ),
                    priority_order:
                        priorityOrder,
                    selected_action:
                        selectedAction.value,
                    written_reply:
                        reply
                };

                hiddenAnswer.value =
                    JSON.stringify(responseData);
            }
        );

        restoreSavedResponse();
    }

    /*
     * Run whether the script loads before or after
     * DOMContentLoaded.
     */
    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializeInboxTask
        );
    } else {
        initializeInboxTask();
    }
})();