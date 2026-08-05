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

        if (!hiddenAnswer || !form) {
            return;
        }

        const checklistBoxes = Array.from(
            document.querySelectorAll(".fe-checklist-item")
        );

        const state = {
            previewCompleted: false,
        };

        function getCheckedItems() {
            return REQUIRED_CHECKLIST.filter((item) =>
                checklistBoxes.some(
                    (box) => box.value === item && box.checked
                )
            );
        }

        function issueStatus() {
            return statusSelect && statusSelect.value
                ? statusSelect.value
                : "needs_further_testing";
        }

        function recommendation() {
            return recommendationSelect &&
                recommendationSelect.value
                ? recommendationSelect.value
                : "needs_more_testing";
        }

        function value(el) {
            return el ? el.value.trim() : "";
        }

        function buildMessage() {
            return [
                "Issue status: " +
                    STATUS_LABELS[issueStatus()],
                "",
                "Root cause:",
                value(rootCause) || "(not provided)",
                "",
                "Fix implemented:",
                value(fixSummary) || "(not provided)",
                "",
                "Browser testing completed:",
                value(testingSummary) || "(not provided)",
                "",
                "Accessibility and responsive design:",
                value(accessibilitySummary) || "(not provided)",
                "",
                "Release recommendation: " +
                    RECOMMENDATION_LABELS[recommendation()],
            ].join("\n");
        }

        if (previewButton) {
            previewButton.addEventListener("click", () => {
                if (previewArea) {
                    previewArea.textContent = buildMessage();
                }

                state.previewCompleted = true;

                if (statusText) {
                    statusText.textContent =
                        "Message previewed. You can send the " +
                        "update or keep editing.";
                    statusText.classList.add("fe-status--ok");
                    statusText.classList.remove("fe-status--bad");
                }
            });
        }

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

            if (statusSelect) {
                statusSelect.value = saved.issue_status || "";
            }

            if (rootCause) {
                rootCause.value = saved.root_cause || "";
            }

            if (fixSummary) {
                fixSummary.value = saved.fix_summary || "";
            }

            if (testingSummary) {
                testingSummary.value =
                    saved.testing_summary || "";
            }

            if (accessibilitySummary) {
                accessibilitySummary.value =
                    saved.accessibility_summary || "";
            }

            if (recommendationSelect) {
                recommendationSelect.value =
                    saved.release_recommendation || "";
            }

            if (Array.isArray(saved.checklist)) {
                checklistBoxes.forEach((box) => {
                    box.checked = saved.checklist.includes(
                        box.value
                    );
                });
            }

            if (previewArea) {
                previewArea.textContent = buildMessage();
            }

            state.previewCompleted = Boolean(
                saved.preview_completed
            );
        }

        form.addEventListener("submit", () => {
            const checklist = getCheckedItems();

            const payload = {
                task_type: "frontend_team_chat",
                channel: "frontend-releases",
                recipient: {
                    id: "frontend_team_lead",
                    name: "Maya Lewis",
                    role: "Frontend Team Lead",
                },
                issue_id: "FE-4021",
                issue_status: issueStatus(),
                checklist: checklist,
                root_cause: value(rootCause),
                fix_summary: value(fixSummary),
                testing_summary: value(testingSummary),
                accessibility_summary: value(
                    accessibilitySummary
                ),
                release_recommendation: recommendation(),
                message: buildMessage(),
                preview_completed: state.previewCompleted,
                all_required_items_confirmed:
                    checklist.length === REQUIRED_CHECKLIST.length,
            };

            hiddenAnswer.value = JSON.stringify(payload);
        });

        restoreSavedAnswer();
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