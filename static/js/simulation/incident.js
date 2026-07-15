(() => {
    "use strict";

    function initializeIncidentTask() {
        const form = document.getElementById(
            "incident-task-form"
        );

        // Other simulation steps do not contain this form.
        if (!form) {
            return;
        }

        const hiddenAnswer = document.getElementById(
            "answer"
        );

        const findingTextarea = document.getElementById(
            "incident-finding"
        );

        const characterCount = document.getElementById(
            "finding-character-count"
        );

        if (
            !hiddenAnswer ||
            !findingTextarea
        ) {
            console.error(
                "CareerGrid incident task could not start."
            );

            return;
        }

        function updateCharacterCount() {
            const currentLength =
                findingTextarea.value.length;

            if (characterCount) {
                characterCount.textContent =
                    `${currentLength} / 1500`;
            }
        }

        function restoreSavedAnswer() {
            const savedValue =
                hiddenAnswer.dataset.savedAnswer;

            if (!savedValue) {
                updateCharacterCount();
                return;
            }

            try {
                const savedResponse =
                    JSON.parse(savedValue);

                if (
                    !savedResponse ||
                    typeof savedResponse !== "object"
                ) {
                    return;
                }

                findingTextarea.value =
                    savedResponse.technical_finding || "";

                const selectedRootCause =
                    savedResponse.selected_root_cause;

                if (selectedRootCause) {
                    const matchingOption =
                        form.querySelector(
                            `input[name="selected_root_cause"][value="${selectedRootCause}"]`
                        );

                    if (matchingOption) {
                        matchingOption.checked = true;
                    }
                }

            } catch (error) {
                /*
                 * Ignore older plain-text Step 2 answers.
                 * They were saved before the interactive task existed.
                 */
            }

            updateCharacterCount();
        }

        findingTextarea.addEventListener(
            "input",
            () => {
                findingTextarea.setCustomValidity("");
                updateCharacterCount();
            }
        );

        form.addEventListener(
            "submit",
            (event) => {
                const selectedRootCause =
                    form.querySelector(
                        'input[name="selected_root_cause"]:checked'
                    );

                const technicalFinding =
                    findingTextarea.value.trim();

                if (!selectedRootCause) {
                    event.preventDefault();

                    const firstOption =
                        form.querySelector(
                            'input[name="selected_root_cause"]'
                        );

                    if (firstOption) {
                        firstOption.focus();
                        firstOption.reportValidity();
                    }

                    return;
                }

                if (technicalFinding.length < 20) {
                    event.preventDefault();

                    findingTextarea.setCustomValidity(
                        "Please write a technical finding of at least 20 characters."
                    );

                    findingTextarea.reportValidity();
                    findingTextarea.focus();

                    return;
                }

                if (technicalFinding.length > 1500) {
                    event.preventDefault();

                    findingTextarea.setCustomValidity(
                        "Your technical finding must contain no more than 1500 characters."
                    );

                    findingTextarea.reportValidity();
                    findingTextarea.focus();

                    return;
                }

                findingTextarea.setCustomValidity("");

                const responseData = {
                    task_type: "incident_investigation",
                    incident_id: "INC-2048",
                    selected_root_cause:
                        selectedRootCause.value,
                    technical_finding:
                        technicalFinding
                };

                hiddenAnswer.value =
                    JSON.stringify(responseData);
            }
        );

        restoreSavedAnswer();
    }

    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializeIncidentTask
        );
    } else {
        initializeIncidentTask();
    }
})();