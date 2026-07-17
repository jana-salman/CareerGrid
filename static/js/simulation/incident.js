(() => {
    "use strict";

    function initializeGuidedIncident() {
        const form =
            document.getElementById(
                "guided-incident-form"
            );

        if (!form) {
            return;
        }

        const hiddenAnswer =
            document.getElementById("answer");

        const inspectLogButton =
            document.getElementById(
                "inspect-log-button"
            );

        const comparePayloadsButton =
            document.getElementById(
                "compare-payloads-button"
            );

        const traceCodeButton =
            document.getElementById(
                "trace-code-button"
            );

        const logResult =
            document.getElementById(
                "server-log-result"
            );

        const payloadResult =
            document.getElementById(
                "payload-comparison-result"
            );

        const codeResult =
            document.getElementById(
                "code-trace-result"
            );

        const missingFieldSelect =
            document.getElementById(
                "diagnosis-missing-field"
            );

        const failureMechanismSelect =
            document.getElementById(
                "diagnosis-failure-mechanism"
            );

        const currentStatusSelect =
            document.getElementById(
                "diagnosis-current-status"
            );

        const recommendedFixSelect =
            document.getElementById(
                "diagnosis-recommended-fix"
            );

        const testDiagnosisButton =
            document.getElementById(
                "test-diagnosis-button"
            );

        const diagnosisFeedback =
            document.getElementById(
                "diagnosis-feedback"
            );

        const diagnosisFeedbackIcon =
            document.getElementById(
                "diagnosis-feedback-icon"
            );

        const diagnosisFeedbackTitle =
            document.getElementById(
                "diagnosis-feedback-title"
            );

        const diagnosisFeedbackText =
            document.getElementById(
                "diagnosis-feedback-text"
            );

        const showHintButton =
            document.getElementById(
                "show-diagnosis-hint-button"
            );

        const diagnosisHint =
            document.getElementById(
                "diagnosis-hint"
            );

        const applyGuidedButton =
            document.getElementById(
                "apply-guided-diagnosis-button"
            );

        const findingTextarea =
            document.getElementById(
                "incident-finding"
            );

        const characterCount =
            document.getElementById(
                "finding-character-count"
            );

        const findingRequirementText =
            document.getElementById(
                "finding-requirement-text"
            );

        const statusContainer =
            document.getElementById(
                "guided-incident-status"
            );

        const statusText =
            document.getElementById(
                "guided-status-text"
            );

        const progressValue =
            document.getElementById(
                "guided-progress-value"
            );

        const progressFill =
            document.getElementById(
                "guided-progress-fill"
            );

        const progressDescription =
            document.getElementById(
                "guided-progress-description"
            );

        const submitButton =
            document.getElementById(
                "submit-guided-investigation-button"
            );

        const requiredElements = [
            hiddenAnswer,
            inspectLogButton,
            comparePayloadsButton,
            traceCodeButton,
            missingFieldSelect,
            failureMechanismSelect,
            currentStatusSelect,
            recommendedFixSelect,
            testDiagnosisButton,
            findingTextarea,
            submitButton
        ];

        if (
            requiredElements.some(
                (element) => !element
            )
        ) {
            console.error(
                "CareerGrid guided incident task could not start."
            );

            return;
        }

        const completedActions = new Set();

        let diagnosisAttempts = 0;
        let incorrectDiagnosisAttempts = 0;
        let hintsUsed = 0;
        let guidedDiagnosisUsed = false;
        let diagnosisCompleted = false;

        const diagnosisSelects = [
            missingFieldSelect,
            failureMechanismSelect,
            currentStatusSelect,
            recommendedFixSelect
        ];

        function getStepElements(stepName) {
            return {
                section:
                    document.getElementById(
                        `investigation-step-${stepName}`
                    ),

                state:
                    document.getElementById(
                        `${stepName}-step-state`
                    )
            };
        }

        function setStatus(
            message,
            state = "running"
        ) {
            if (statusText) {
                statusText.textContent = message;
            }

            if (!statusContainer) {
                return;
            }

            statusContainer.classList.remove(
                "is-running",
                "is-complete"
            );

            if (state === "running") {
                statusContainer.classList.add(
                    "is-running"
                );
            }

            if (state === "complete") {
                statusContainer.classList.add(
                    "is-complete"
                );
            }
        }

        function updateProgress(
            percentage,
            description
        ) {
            if (progressValue) {
                progressValue.textContent =
                    `${percentage}%`;
            }

            if (progressFill) {
                progressFill.style.width =
                    `${percentage}%`;
            }

            if (progressDescription) {
                progressDescription.textContent =
                    description;
            }
        }

        function markStepCompleted(stepName) {
            const elements =
                getStepElements(stepName);

            if (elements.section) {
                elements.section.classList.remove(
                    "active",
                    "locked"
                );

                elements.section.classList.add(
                    "completed"
                );
            }

            if (elements.state) {
                elements.state.textContent =
                    "Completed";
            }
        }

        function unlockStep(
            stepName,
            button = null
        ) {
            const elements =
                getStepElements(stepName);

            if (elements.section) {
                elements.section.classList.remove(
                    "locked"
                );

                elements.section.classList.add(
                    "active"
                );
            }

            if (elements.state) {
                elements.state.textContent =
                    "Ready";
            }

            if (button) {
                button.disabled = false;
            }
        }

        function revealResult(element) {
            if (!element) {
                return;
            }

            element.hidden = false;

            element.scrollIntoView({
                behavior: "smooth",
                block: "nearest"
            });
        }

        function completeLogInspection() {
            if (
                completedActions.has(
                    "inspect_logs"
                )
            ) {
                return;
            }

            completedActions.add(
                "inspect_logs"
            );

            revealResult(logResult);

            inspectLogButton.textContent =
                "✓ Log Inspected";

            inspectLogButton.disabled = true;

            markStepCompleted("log");

            unlockStep(
                "payload",
                comparePayloadsButton
            );

            setStatus(
                "Server error identified"
            );

            updateProgress(
                20,
                "Next: compare the successful and failed requests."
            );
        }

        function completePayloadComparison() {
            if (
                completedActions.has(
                    "compare_payloads"
                )
            ) {
                return;
            }

            completedActions.add(
                "compare_payloads"
            );

            revealResult(payloadResult);

            comparePayloadsButton.textContent =
                "✓ Requests Compared";

            comparePayloadsButton.disabled = true;

            markStepCompleted("payload");

            unlockStep(
                "code",
                traceCodeButton
            );

            setStatus(
                "Request difference identified"
            );

            updateProgress(
                40,
                "Next: trace the failing backend code."
            );
        }

        function completeCodeTrace() {
            if (
                completedActions.has(
                    "trace_code"
                )
            ) {
                return;
            }

            completedActions.add(
                "trace_code"
            );

            revealResult(codeResult);

            traceCodeButton.textContent =
                "✓ Failing Code Traced";

            traceCodeButton.disabled = true;

            markStepCompleted("code");

            unlockStep("diagnosis");

            diagnosisSelects.forEach(
                (select) => {
                    select.disabled = false;
                }
            );

            setStatus(
                "Evidence collected — build your diagnosis"
            );

            updateProgress(
                60,
                "Next: build and test your diagnosis."
            );

            updateDiagnosisButton();
        }

        function diagnosisIsComplete() {
            return diagnosisSelects.every(
                (select) => Boolean(select.value)
            );
        }

        function updateDiagnosisButton() {
            if (diagnosisCompleted) {
                return;
            }

            testDiagnosisButton.disabled =
                !diagnosisIsComplete();
        }

        function getDiagnosisFeedback() {
            if (
                missingFieldSelect.value !==
                "product_id"
            ) {
                return (
                    "Review the two request payloads. " +
                    "Which field exists in the successful request " +
                    "but is absent from the failed request?"
                );
            }

            if (
                failureMechanismSelect.value !==
                "unsafe_dictionary_access"
            ) {
                return (
                    "Review the highlighted Python line. " +
                    "Consider what happens when dictionary bracket " +
                    "access is used for a missing key."
                );
            }

            if (
                currentStatusSelect.value !==
                "500"
            ) {
                return (
                    "Review the production incident details. " +
                    "The unhandled backend exception currently causes " +
                    "an internal server error."
                );
            }

            return (
                "The proposed action does not prevent the invalid " +
                "payload from reaching the unsafe code. Review how " +
                "the API should respond to invalid client input."
            );
        }

        function showDiagnosisFeedback(
            isCorrect,
            title,
            message
        ) {
            if (!diagnosisFeedback) {
                return;
            }

            diagnosisFeedback.hidden = false;

            diagnosisFeedback.classList.remove(
                "success",
                "error"
            );

            diagnosisFeedback.classList.add(
                isCorrect
                    ? "success"
                    : "error"
            );

            if (diagnosisFeedbackIcon) {
                diagnosisFeedbackIcon.textContent =
                    isCorrect ? "✓" : "!";
            }

            if (diagnosisFeedbackTitle) {
                diagnosisFeedbackTitle.textContent =
                    title;
            }

            if (diagnosisFeedbackText) {
                diagnosisFeedbackText.textContent =
                    message;
            }
        }

        function diagnosisIsCorrect() {
            return (
                missingFieldSelect.value ===
                    "product_id" &&

                failureMechanismSelect.value ===
                    "unsafe_dictionary_access" &&

                currentStatusSelect.value ===
                    "500" &&

                recommendedFixSelect.value ===
                    "validate_product_id"
            );
        }

        function confirmDiagnosis() {
            diagnosisCompleted = true;

            markStepCompleted("diagnosis");

            diagnosisSelects.forEach(
                (select) => {
                    select.disabled = true;
                }
            );

            testDiagnosisButton.disabled = true;
            testDiagnosisButton.textContent =
                "✓ Diagnosis Confirmed";

            showDiagnosisFeedback(
                true,
                "Diagnosis confirmed",
                "The failed request is missing product_id. " +
                "Direct dictionary access raises an unhandled " +
                "KeyError and causes HTTP 500. Validating the field " +
                "should return HTTP 400 for invalid input."
            );

            unlockStep("finding");

            findingTextarea.disabled = false;

            findingTextarea.placeholder =
                "Summarize the root cause, evidence, and recommended action...";

            if (findingRequirementText) {
                findingRequirementText.textContent =
                    "Write at least 20 characters.";
            }

            setStatus(
                "Root cause confirmed"
            );

            updateProgress(
                80,
                "Final step: write your technical finding."
            );

            findingTextarea.focus();

            updateFindingState();
        }

        function testDiagnosis() {
            if (
                diagnosisCompleted ||
                !diagnosisIsComplete()
            ) {
                return;
            }

            diagnosisAttempts += 1;

            if (diagnosisIsCorrect()) {
                confirmDiagnosis();
                return;
            }

            incorrectDiagnosisAttempts += 1;

            showDiagnosisFeedback(
                false,
                "Diagnosis not confirmed",
                getDiagnosisFeedback()
            );

            setStatus(
                "Diagnosis needs revision"
            );

            if (
                incorrectDiagnosisAttempts >= 2 &&
                showHintButton
            ) {
                showHintButton.hidden = false;
            }

            if (
                incorrectDiagnosisAttempts >= 3 &&
                applyGuidedButton
            ) {
                applyGuidedButton.hidden = false;
            }
        }

        function showHint() {
            if (!diagnosisHint) {
                return;
            }

            if (diagnosisHint.hidden) {
                hintsUsed += 1;
            }

            diagnosisHint.hidden = false;

            showHintButton.disabled = true;
            showHintButton.textContent =
                "✓ Hint Shown";
        }

        function applyGuidedDiagnosis() {
            guidedDiagnosisUsed = true;

            missingFieldSelect.value =
                "product_id";

            failureMechanismSelect.value =
                "unsafe_dictionary_access";

            currentStatusSelect.value =
                "500";

            recommendedFixSelect.value =
                "validate_product_id";

            applyGuidedButton.disabled = true;

            applyGuidedButton.textContent =
                "✓ Guided Diagnosis Applied";

            showDiagnosisFeedback(
                false,
                "Guided diagnosis applied",
                "Review the selected values, then test the diagnosis again."
            );

            updateDiagnosisButton();
        }

        function updateCharacterCount() {
            if (characterCount) {
                characterCount.textContent =
                    `${findingTextarea.value.length} / 1500`;
            }

            updateFindingState();
        }

        function updateFindingState() {
            const findingLength =
                findingTextarea.value.trim().length;

            if (
                diagnosisCompleted &&
                findingLength >= 20
            ) {
                submitButton.disabled = false;

                submitButton.textContent =
                    "Submit Investigation";

                markStepCompleted("finding");

                setStatus(
                    "Investigation ready to submit",
                    "complete"
                );

                updateProgress(
                    100,
                    "Investigation complete."
                );
            } else {
                submitButton.disabled = true;

                submitButton.textContent =
                    diagnosisCompleted
                        ? "Complete Your Technical Finding"
                        : "Complete the Investigation First";
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

                const actions =
                    savedResponse.investigation_actions;

                if (
                    Array.isArray(actions) &&
                    actions.includes("inspect_logs")
                ) {
                    completeLogInspection();
                }

                if (
                    Array.isArray(actions) &&
                    actions.includes("compare_payloads")
                ) {
                    completePayloadComparison();
                }

                if (
                    Array.isArray(actions) &&
                    actions.includes("trace_code")
                ) {
                    completeCodeTrace();
                }

                missingFieldSelect.value =
                    savedResponse.selected_missing_field || "";

                failureMechanismSelect.value =
                    savedResponse.selected_failure_mechanism || "";

                currentStatusSelect.value =
                    String(
                        savedResponse.selected_current_status || ""
                    );

                recommendedFixSelect.value =
                    savedResponse.selected_fix || "";

                diagnosisAttempts =
                    Number(
                        savedResponse.diagnosis_attempts
                    ) || 0;

                incorrectDiagnosisAttempts =
                    Number(
                        savedResponse.incorrect_diagnosis_attempts
                    ) || 0;

                hintsUsed =
                    Number(
                        savedResponse.hints_used
                    ) || 0;

                guidedDiagnosisUsed =
                    Boolean(
                        savedResponse.guided_diagnosis_used
                    );

                findingTextarea.value =
                    savedResponse.technical_finding || "";

                if (
                    savedResponse.diagnosis_confirmed === true
                ) {
                    confirmDiagnosis();
                }

            } catch (error) {
                console.warn(
                    "Could not restore the saved incident investigation."
                );
            }

            updateDiagnosisButton();
            updateCharacterCount();
        }

        inspectLogButton.addEventListener(
            "click",
            completeLogInspection
        );

        comparePayloadsButton.addEventListener(
            "click",
            completePayloadComparison
        );

        traceCodeButton.addEventListener(
            "click",
            completeCodeTrace
        );

        diagnosisSelects.forEach(
            (select) => {
                select.addEventListener(
                    "change",
                    updateDiagnosisButton
                );
            }
        );

        testDiagnosisButton.addEventListener(
            "click",
            testDiagnosis
        );

        if (showHintButton) {
            showHintButton.addEventListener(
                "click",
                showHint
            );
        }

        if (applyGuidedButton) {
            applyGuidedButton.addEventListener(
                "click",
                applyGuidedDiagnosis
            );
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
                const technicalFinding =
                    findingTextarea.value.trim();

                if (
                    !diagnosisCompleted ||
                    technicalFinding.length < 20
                ) {
                    event.preventDefault();

                    findingTextarea.setCustomValidity(
                        "Confirm your diagnosis and write at least 20 characters."
                    );

                    findingTextarea.reportValidity();
                    findingTextarea.focus();

                    return;
                }

                findingTextarea.setCustomValidity("");

                const responseData = {
                    task_type:
                        "incident_investigation",

                    incident_id:
                        "INC-2048",

                    selected_root_cause:
                        "missing_product_id",

                    investigation_actions:
                        Array.from(
                            completedActions
                        ),

                    diagnosis_attempts:
                        diagnosisAttempts,

                    incorrect_diagnosis_attempts:
                        incorrectDiagnosisAttempts,

                    diagnostic_runs:
                        diagnosisAttempts,

                    selected_missing_field:
                        missingFieldSelect.value,

                    selected_failure_mechanism:
                        failureMechanismSelect.value,

                    selected_current_status:
                        Number(
                            currentStatusSelect.value
                        ),

                    selected_expected_status:
                        400,

                    selected_fix:
                        recommendedFixSelect.value,

                    hints_used:
                        hintsUsed,

                    guided_diagnosis_used:
                        guidedDiagnosisUsed,

                    diagnosis_confirmed:
                        diagnosisCompleted,

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
            initializeGuidedIncident
        );
    } else {
        initializeGuidedIncident();
    }
})();