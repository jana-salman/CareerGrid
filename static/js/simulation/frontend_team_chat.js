(() => {
    "use strict";

    const REQUIRED_CHECKLIST = [
        "root_cause_identified",
        "selector_fixed",
        "dom_ready_handled",
        "desktop_tested",
        "mobile_tested",
        "keyboard_tested",
    ];

    const STATUS_LABELS = {
        resolved: "Resolved",
        needs_further_testing: "Needs further testing",
        blocked: "Blocked",
    };

    const RECOMMENDATION_LABELS = {
        ready_for_review: "Ready for code review",
        needs_more_testing: "Needs more testing",
        do_not_release: "Do not release",
    };

    function initializeFrontendTeamChat() {
        const form = document.getElementById(
            "frontend-team-chat-form"
        );

        if (!form) {
            return;
        }

        const hiddenAnswer = document.getElementById("answer");
        const statusSelect =
            document.getElementById("fe-issue-status");
        const rootCause =
            document.getElementById("fe-root-cause");
        const fixSummary =
            document.getElementById("fe-fix-summary");
        const testingSummary =
            document.getElementById("fe-testing-summary");
        const accessibilitySummary =
            document.getElementById("fe-accessibility-summary");
        const recommendationSelect =
            document.getElementById("fe-release-recommendation");
        const previewButton =
            document.getElementById("fe-preview-btn");
        const previewArea =
            document.getElementById("fe-message-preview");
        const statusText =
            document.getElementById("fe-team-chat-status");
        const submitButton =
            document.getElementById("fe-team-chat-submit");

        if (
            !hiddenAnswer ||
            !statusSelect ||
            !rootCause ||
            !fixSummary ||
            !testingSummary ||
            !accessibilitySummary ||
            !recommendationSelect ||
            !previewButton ||
            !submitButton
        ) {
            return;
        }

        const checklistBoxes = Array.from(
            document.querySelectorAll(".fe-checklist-item")
        );

        const state = {
            previewCompleted: false,
        };

        function getCheckedItems() {
            return checklistBoxes
                .filter((box) => box.checked)
                .map((box) => box.value);
        }

        function summariesValid() {
            return (
                rootCause.value.trim().length >= 25 &&
                fixSummary.value.trim().length >= 25 &&
                testingSummary.value.trim().length >= 25 &&
                accessibilitySummary.value.trim().length >= 25
            );
        }

        function checklistComplete() {
            const checked = new Set(getCheckedItems());

            return REQUIRED_CHECKLIST.every((item) =>
                checked.has(item)
            );
        }

        function formIsValid() {
            return (
                Boolean(STATUS_LABELS[statusSelect.value]) &&
                Boolean(
                    RECOMMENDATION_LABELS[
                        recommendationSelect.value
                    ]
                ) &&
                checklistComplete() &&
                summariesValid()
            );
        }

        function buildMessage() {
            return [
                "Issue status: " +
                    STATUS_LABELS[statusSelect.value],
                "",
                "Root cause:",
                rootCause.value.trim(),
                "",
                "Fix implemented:",
                fixSummary.value.trim(),
                "",
                "Browser testing completed:",
                testingSummary.value.trim(),
                "",
                "Accessibility and responsive design:",
                accessibilitySummary.value.trim(),
                "",
                "Release recommendation: " +
                    RECOMMENDATION_LABELS[
                        recommendationSelect.value
                    ],
            ].join("\n");
        }

        function updateSubmitState() {
            submitButton.disabled = !(
                state.previewCompleted && formIsValid()
            );
        }

        previewButton.addEventListener("click", () => {
            if (!formIsValid()) {
                state.previewCompleted = false;

                if (statusText) {
                    statusText.textContent =
                        "Complete every field, confirm all six " +
                        "checklist items, and write at least 25 " +
                        "characters in each summary before " +
                        "previewing.";
                    statusText.classList.add("fe-status--bad");
                    statusText.classList.remove("fe-status--ok");
                }

                updateSubmitState();
                return;
            }

            if (previewArea) {
                previewArea.textContent = buildMessage();
            }

            state.previewCompleted = true;

            if (statusText) {
                statusText.textContent =
                    "Message previewed. You can send the update.";
                statusText.classList.add("fe-status--ok");
                statusText.classList.remove("fe-status--bad");
            }

            updateSubmitState();
        });

        // Editing any field requires a fresh preview.
        const watched = [
            statusSelect,
            rootCause,
            fixSummary,
            testingSummary,
            accessibilitySummary,
            recommendationSelect,
        ];

        watched.forEach((field) => {
            field.addEventListener("input", () => {
                state.previewCompleted = false;
                updateSubmitState();
            });
        });

        checklistBoxes.forEach((box) => {
            box.addEventListener("change", () => {
                state.previewCompleted = false;
                updateSubmitState();
            });
        });

        function restoreSavedAnswer() {
            const raw = (
                hiddenAnswer.getAttribute("data-saved-answer") || ""
            ).trim();

            if (!raw) {
                return;
            }

            let saved = null;

            try {
                const first = JSON.parse(raw);
                saved =
                    typeof first === "string"
                        ? JSON.parse(first)
                        : first;
            } catch (error) {
                saved = null;
            }

            if (!saved || typeof saved !== "object") {
                return;
            }

            statusSelect.value = saved.issue_status || "";
            rootCause.value = saved.root_cause || "";
            fixSummary.value = saved.fix_summary || "";
            testingSummary.value = saved.testing_summary || "";
            accessibilitySummary.value =
                saved.accessibility_summary || "";
            recommendationSelect.value =
                saved.release_recommendation || "";

            if (Array.isArray(saved.checklist)) {
                checklistBoxes.forEach((box) => {
                    box.checked = saved.checklist.includes(
                        box.value
                    );
                });
            }

            if (formIsValid() && previewArea) {
                previewArea.textContent = buildMessage();
                state.previewCompleted = Boolean(
                    saved.preview_completed
                );
            }

            updateSubmitState();
        }

        form.addEventListener("submit", (event) => {
            if (!formIsValid()) {
                event.preventDefault();
                state.previewCompleted = false;
                updateSubmitState();
                return;
            }

            if (!state.previewCompleted && previewArea) {
                previewArea.textContent = buildMessage();
                state.previewCompleted = true;
            }

            const payload = {
                task_type: "frontend_team_chat",
                channel: "frontend-releases",
                recipient: {
                    id: "frontend_team_lead",
                    name: "Maya Lewis",
                    role: "Frontend Team Lead",
                },
                issue_id: "FE-4021",
                issue_status: statusSelect.value,
                checklist: REQUIRED_CHECKLIST.slice(),
                root_cause: rootCause.value.trim(),
                fix_summary: fixSummary.value.trim(),
                testing_summary: testingSummary.value.trim(),
                accessibility_summary:
                    accessibilitySummary.value.trim(),
                release_recommendation:
                    recommendationSelect.value,
                message: buildMessage(),
                preview_completed: true,
                all_required_items_confirmed: true,
            };

            hiddenAnswer.value = JSON.stringify(payload);
        });

        restoreSavedAnswer();
        updateSubmitState();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeFrontendTeamChat
        );
    } else {
        initializeFrontendTeamChat();
    }
})();