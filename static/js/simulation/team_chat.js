(() => {
    "use strict";

    function initializeTeamChatWorkspace() {
        const form = document.getElementById(
            "team-chat-form"
        );

        // Other simulation steps do not contain this form.
        if (!form) {
            return;
        }

        const hiddenAnswer =
            document.getElementById("answer");

        const incidentStatus =
            document.getElementById(
                "incident-status"
            );

        const rootCause =
            document.getElementById(
                "root-cause"
            );

        const fixSummary =
            document.getElementById(
                "fix-summary"
            );

        const testingSummary =
            document.getElementById(
                "testing-summary"
            );

        const releaseRecommendation =
            document.getElementById(
                "release-recommendation"
            );

        const checklistInputs = Array.from(
            document.querySelectorAll(
                ".team-chat-check-item input"
            )
        );

        const previewButton =
            document.getElementById(
                "preview-team-update-button"
            );

        const submitButton =
            document.getElementById(
                "submit-team-chat-button"
            );

        const previewSection =
            document.getElementById(
                "team-chat-preview"
            );

        const previewContent =
            document.getElementById(
                "team-chat-preview-content"
            );

        const completionStatus =
            document.querySelector(
                ".team-chat-completion-status"
            );

        const statusText =
            document.getElementById(
                "team-chat-status-text"
            );

        const requiredElements = [
            hiddenAnswer,
            incidentStatus,
            rootCause,
            fixSummary,
            testingSummary,
            releaseRecommendation,
            previewButton,
            submitButton,
            previewSection,
            previewContent,
        ];

        if (
            requiredElements.some(
                (element) => !element
            )
        ) {
            console.error(
                "CareerGrid team chat workspace could not start."
            );

            return;
        }

        const requiredChecklistItems = [
            "root_cause_identified",
            "fix_implemented",
            "valid_payload_tested",
            "invalid_payload_tested",
            "server_error_prevented",
        ];

        let previewIsCurrent = false;

        function getCheckedItems() {
            return checklistInputs
                .filter((input) => input.checked)
                .map((input) => input.value);
        }

        function allChecklistItemsAreChecked() {
            const checkedItems =
                getCheckedItems();

            return requiredChecklistItems.every(
                (requiredItem) =>
                    checkedItems.includes(
                        requiredItem
                    )
            );
        }

        function textHasEnoughDetail(
            textarea
        ) {
            return (
                textarea.value.trim().length >= 25
            );
        }

        function draftIsComplete() {
            return Boolean(
                incidentStatus.value &&
                releaseRecommendation.value &&
                allChecklistItemsAreChecked() &&
                textHasEnoughDetail(rootCause) &&
                textHasEnoughDetail(fixSummary) &&
                textHasEnoughDetail(
                    testingSummary
                )
            );
        }

        function getIncidentStatusLabel() {
            const selectedOption =
                incidentStatus.options[
                    incidentStatus.selectedIndex
                ];

            return selectedOption
                ? selectedOption.text.trim()
                : "";
        }

        function getRecommendationLabel() {
            const selectedOption =
                releaseRecommendation.options[
                    releaseRecommendation
                        .selectedIndex
                ];

            return selectedOption
                ? selectedOption.text.trim()
                : "";
        }

        function buildPreviewMessage() {
            return [
                `Incident status: ${getIncidentStatusLabel()}`,
                "",
                "Root cause:",
                rootCause.value.trim(),
                "",
                "Fix implemented:",
                fixSummary.value.trim(),
                "",
                "Testing completed:",
                testingSummary.value.trim(),
                "",
                `Release recommendation: ${getRecommendationLabel()}`,
            ].join("\n");
        }

        function buildStructuredAnswer() {
            return {
                task_type: "team_chat",

                channel: "backend-releases",

                recipient: {
                    id: "backend_team_lead",
                    name: "Alex Carter",
                    role: "Backend Team Lead",
                },

                incident_id: "INC-2048",

                incident_status:
                    incidentStatus.value,

                checklist:
                    getCheckedItems(),

                root_cause:
                    rootCause.value.trim(),

                fix_summary:
                    fixSummary.value.trim(),

                testing_summary:
                    testingSummary.value.trim(),

                release_recommendation:
                    releaseRecommendation.value,

                message:
                    buildPreviewMessage(),

                preview_completed:
                    previewIsCurrent,

                all_required_items_confirmed:
                    allChecklistItemsAreChecked(),
            };
        }

        function updateHiddenAnswer() {
            hiddenAnswer.value =
                JSON.stringify(
                    buildStructuredAnswer()
                );
        }

        function markPreviewAsOutdated() {
            previewIsCurrent = false;

            previewSection.hidden = true;
            submitButton.disabled = true;

            if (completionStatus) {
                completionStatus.classList.remove(
                    "message-ready"
                );
            }
        }

        function updateWorkspaceStatus() {
            const complete =
                draftIsComplete();

            previewButton.disabled =
                !complete;

            if (!complete) {
                markPreviewAsOutdated();

                if (statusText) {
                    statusText.textContent =
                        "Draft incomplete";
                }
            } else if (!previewIsCurrent) {
                submitButton.disabled = true;

                if (statusText) {
                    statusText.textContent =
                        "Ready to preview";
                }

                if (completionStatus) {
                    completionStatus.classList.remove(
                        "message-ready"
                    );
                }
            } else {
                submitButton.disabled = false;

                if (statusText) {
                    statusText.textContent =
                        "Ready to send";
                }

                if (completionStatus) {
                    completionStatus.classList.add(
                        "message-ready"
                    );
                }
            }

            updateHiddenAnswer();
        }

        function handleDraftChange() {
            markPreviewAsOutdated();
            updateWorkspaceStatus();
        }

        function showPreview() {
            if (!draftIsComplete()) {
                return;
            }

            previewContent.textContent =
                buildPreviewMessage();

            previewSection.hidden = false;
            previewIsCurrent = true;

            updateWorkspaceStatus();

            previewSection.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
            });
        }

        function restoreSavedAnswer() {
            const savedAnswer =
                hiddenAnswer.dataset.savedAnswer;

            if (!savedAnswer) {
                updateWorkspaceStatus();
                return;
            }

            try {
                const parsedAnswer =
                    JSON.parse(savedAnswer);

                incidentStatus.value =
                    parsedAnswer.incident_status ||
                    "";

                rootCause.value =
                    parsedAnswer.root_cause ||
                    "";

                fixSummary.value =
                    parsedAnswer.fix_summary ||
                    "";

                testingSummary.value =
                    parsedAnswer.testing_summary ||
                    "";

                releaseRecommendation.value =
                    parsedAnswer
                        .release_recommendation ||
                    "";

                const savedChecklist =
                    Array.isArray(
                        parsedAnswer.checklist
                    )
                        ? parsedAnswer.checklist
                        : [];

                checklistInputs.forEach(
                    (input) => {
                        input.checked =
                            savedChecklist.includes(
                                input.value
                            );
                    }
                );

                previewIsCurrent =
                    parsedAnswer
                        .preview_completed === true &&
                    draftIsComplete();

                if (previewIsCurrent) {
                    previewContent.textContent =
                        buildPreviewMessage();

                    previewSection.hidden = false;
                }
            } catch (error) {
                console.warn(
                    "The saved team update could not be restored.",
                    error
                );
            }

            updateWorkspaceStatus();
        }

        const textInputs = [
            rootCause,
            fixSummary,
            testingSummary,
        ];

        textInputs.forEach((textarea) => {
            textarea.addEventListener(
                "input",
                handleDraftChange
            );
        });

        incidentStatus.addEventListener(
            "change",
            handleDraftChange
        );

        releaseRecommendation.addEventListener(
            "change",
            handleDraftChange
        );

        checklistInputs.forEach((input) => {
            input.addEventListener(
                "change",
                handleDraftChange
            );
        });

        previewButton.addEventListener(
            "click",
            showPreview
        );

        form.addEventListener(
            "submit",
            (event) => {
                if (
                    !draftIsComplete() ||
                    !previewIsCurrent
                ) {
                    event.preventDefault();

                    if (statusText) {
                        statusText.textContent =
                            "Preview your final update first";
                    }

                    return;
                }

                updateHiddenAnswer();
            }
        );

        restoreSavedAnswer();
    }

    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializeTeamChatWorkspace
        );
    } else {
        initializeTeamChatWorkspace();
    }
})();