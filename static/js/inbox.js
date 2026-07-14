document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("inbox-task-form");

    // This file is loaded on other pages too, so stop when the
    // interactive inbox is not present.
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
        document.getElementById("reply-validation-message");

    const priorityList =
        document.getElementById("priority-list");

    const mailItems = Array.from(
        document.querySelectorAll(".mail-item")
    );

    let emails = [];
    let savedResponse = null;
    let draggedItem = null;

    const openedEmailIds = new Set();

    try {
        emails = JSON.parse(
            inboxDataElement.textContent
        );
    } catch (error) {
        console.error(
            "Could not read generated inbox data:",
            error
        );
        return;
    }

    /*
     * saved-inbox-answer contains a JSON-encoded string.
     * The first parse retrieves the string.
     * The second parse retrieves the saved response object.
     */
    try {
        const savedAnswerString = JSON.parse(
            savedAnswerElement.textContent
        );

        if (savedAnswerString) {
            savedResponse = JSON.parse(savedAnswerString);
        }
    } catch (error) {
        // This is normal when no previous answer exists.
        savedResponse = null;
    }

    const findEmail = (emailId) => {
        return emails.find(
            (email) => email.id === emailId
        );
    };

    const displayEmail = (emailId) => {
        const email = findEmail(emailId);

        if (!email) {
            return;
        }

        openedEmailIds.add(emailId);

        mailItems.forEach((item) => {
            item.classList.toggle(
                "active",
                item.dataset.emailId === emailId
            );
        });

        document.getElementById(
            "active-email-subject"
        ).textContent = email.subject;

        document.getElementById(
            "active-email-time"
        ).textContent = email.timestamp;

        document.getElementById(
            "active-email-sender"
        ).textContent = email.sender_name;

        document.getElementById(
            "active-email-role"
        ).textContent = email.sender_role;

        document.getElementById(
            "active-email-avatar"
        ).textContent = email.sender_name
            ? email.sender_name.charAt(0).toUpperCase()
            : "?";

        document.getElementById(
            "active-email-body"
        ).textContent = email.body;

        const attachmentContainer =
            document.getElementById(
                "active-email-attachment"
            );

        const attachmentName =
            document.getElementById(
                "active-attachment-name"
            );

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

        const ticketContainer =
            document.getElementById(
                "active-email-ticket"
            );

        const ticketId =
            document.getElementById(
                "active-ticket-id"
            );

        if (email.linked_ticket_id) {
            ticketContainer.hidden = false;
            ticketId.textContent =
                email.linked_ticket_id;
        } else {
            ticketContainer.hidden = true;
            ticketId.textContent = "";
        }
    };

    mailItems.forEach((item) => {
        item.addEventListener("click", () => {
            displayEmail(item.dataset.emailId);
        });
    });

    const updatePriorityRanks = () => {
        const priorityItems = Array.from(
            priorityList.querySelectorAll(
                ".priority-item"
            )
        );

        priorityItems.forEach((item, index) => {
            const rank =
                item.querySelector(".priority-rank");

            rank.textContent = index + 1;
        });
    };

    const moveItemUp = (item) => {
        const previousItem =
            item.previousElementSibling;

        if (previousItem) {
            priorityList.insertBefore(
                item,
                previousItem
            );

            updatePriorityRanks();
        }
    };

    const moveItemDown = (item) => {
        const nextItem =
            item.nextElementSibling;

        if (nextItem) {
            priorityList.insertBefore(
                nextItem,
                item
            );

            updatePriorityRanks();
        }
    };

    priorityList.addEventListener("click", (event) => {
        const priorityItem =
            event.target.closest(".priority-item");

        if (!priorityItem) {
            return;
        }

        if (
            event.target.closest(".move-priority-up")
        ) {
            moveItemUp(priorityItem);
        }

        if (
            event.target.closest(".move-priority-down")
        ) {
            moveItemDown(priorityItem);
        }
    });

    priorityList.addEventListener(
        "dragstart",
        (event) => {
            draggedItem =
                event.target.closest(".priority-item");

            if (!draggedItem) {
                return;
            }

            draggedItem.classList.add("dragging");

            event.dataTransfer.effectAllowed = "move";
        }
    );

    priorityList.addEventListener(
        "dragend",
        () => {
            if (draggedItem) {
                draggedItem.classList.remove("dragging");
            }

            draggedItem = null;
            updatePriorityRanks();
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
                event.target.closest(".priority-item");

            if (
                !targetItem ||
                targetItem === draggedItem
            ) {
                return;
            }

            const targetBox =
                targetItem.getBoundingClientRect();

            const placeAfter =
                event.clientY >
                targetBox.top + targetBox.height / 2;

            if (placeAfter) {
                targetItem.after(draggedItem);
            } else {
                targetItem.before(draggedItem);
            }
        }
    );

    const restoreSavedResponse = () => {
        if (!savedResponse) {
            displayEmail(emails[0].id);
            return;
        }

        if (
            Array.isArray(savedResponse.opened_emails)
        ) {
            savedResponse.opened_emails.forEach(
                (emailId) => {
                    openedEmailIds.add(emailId);
                }
            );
        }

        if (
            Array.isArray(savedResponse.priority_order)
        ) {
            savedResponse.priority_order.forEach(
                (emailId) => {
                    const priorityItem =
                        priorityList.querySelector(
                            `[data-email-id="${emailId}"]`
                        );

                    if (priorityItem) {
                        priorityList.appendChild(
                            priorityItem
                        );
                    }
                }
            );

            updatePriorityRanks();
        }

        const actionOptions = Array.from(
            document.querySelectorAll(
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

        const lastOpenedEmail =
            savedResponse.opened_emails?.at(-1);

        displayEmail(
            findEmail(lastOpenedEmail)
                ? lastOpenedEmail
                : emails[0].id
        );
    };

    replyTextarea.addEventListener("input", () => {
        replyTextarea.setCustomValidity("");
        replyValidationMessage.hidden = true;
    });

    form.addEventListener("submit", (event) => {
        const reply = replyTextarea.value.trim();

        if (reply.length < 15) {
            event.preventDefault();

            replyTextarea.setCustomValidity(
                "Please write a meaningful professional reply."
            );

            replyValidationMessage.hidden = false;
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
            return;
        }

        const priorityOrder = Array.from(
            priorityList.querySelectorAll(
                ".priority-item"
            )
        ).map((item) => item.dataset.emailId);

        const responseData = {
            task_type: "inbox",
            opened_emails: Array.from(openedEmailIds),
            priority_order: priorityOrder,
            selected_action: selectedAction.value,
            written_reply: reply
        };

        hiddenAnswer.value =
            JSON.stringify(responseData);
    });

    restoreSavedResponse();
});