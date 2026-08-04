(() => {
    "use strict";

    const CORRECT = {
        html_id: "buy-now-btn",
        js_selector: "#checkout-btn",
        root_cause: "selector_id_mismatch",
        null_reason: "element_not_found",
        failure_mechanism: "addeventlistener_on_null",
    };

    function initializeFrontendInvestigation() {
        const form = document.getElementById(
            "frontend-investigation-form"
        );

        if (!form) {
            return;
        }

        const hiddenAnswer = document.getElementById("answer");
        const htmlIdSelect = document.getElementById("fe-html-id");
        const jsSelectorSelect =
            document.getElementById("fe-js-selector");
        const runButton =
            document.getElementById("fe-run-diagnosis");
        const hintButton =
            document.getElementById("fe-investigation-hint");
        const hintText =
            document.getElementById("fe-investigation-hint-text");
        const guidedButton =
            document.getElementById("fe-guided-diagnosis");
        const statusText =
            document.getElementById("fe-diagnosis-status");
        const findingInput =
            document.getElementById("fe-technical-finding");
        const findingValidation =
            document.getElementById("fe-finding-validation");
        const submitButton =
            document.getElementById("fe-investigation-submit");

        if (
            !hiddenAnswer ||
            !htmlIdSelect ||
            !jsSelectorSelect ||
            !runButton ||
            !findingInput ||
            !submitButton
        ) {
            return;
        }

        const evidenceToggles = Array.from(
            document.querySelectorAll(".fe-evidence-toggle")
        );

        const actionCheckboxes = Array.from(
            document.querySelectorAll(".fe-action-checkbox")
        );

        const openedEvidence = new Set();

        const state = {
            diagnosisAttempts: 0,
            incorrectDiagnosisAttempts: 0,
            diagnosticRuns: 0,
            hintsUsed: 0,
            guidedDiagnosisUsed: false,
            diagnosisConfirmed: false,
        };

        function getSelectedRadio(name) {
            const selected = form.querySelector(
                `input[name="${name}"]:checked`
            );

            return selected ? selected.value : "";
        }

        function getSelectedActions() {
            return actionCheckboxes
                .filter((box) => box.checked)
                .map((box) => box.value);
        }

        function selectionsAreCorrect() {
            return (
                htmlIdSelect.value === CORRECT.html_id &&
                jsSelectorSelect.value === CORRECT.js_selector &&
                getSelectedRadio("fe_root_cause") ===
                    CORRECT.root_cause &&
                getSelectedRadio("fe_null_reason") ===
                    CORRECT.null_reason &&
                getSelectedRadio("fe_failure_mechanism") ===
                    CORRECT.failure_mechanism
            );
        }

        function findingIsValid() {
            return findingInput.value.trim().length >= 20;
        }

        function updateSubmitState() {
            const ready =
                state.diagnosisConfirmed &&
                getSelectedActions().length === 3 &&
                findingIsValid();

            submitButton.disabled = !ready;
        }

        // Evidence open/close.
        evidenceToggles.forEach((toggle) => {
            toggle.addEventListener("click", () => {
                const body = toggle.nextElementSibling;
                const evidenceId = toggle.getAttribute(
                    "data-evidence-id"
                );

                const isHidden = body.hasAttribute("hidden");

                if (isHidden) {
                    body.removeAttribute("hidden");
                    toggle.setAttribute("aria-expanded", "true");
                } else {
                    body.setAttribute("hidden", "");
                    toggle.setAttribute("aria-expanded", "false");
                }

                if (evidenceId) {
                    openedEvidence.add(evidenceId);
                }
            });
        });

        // Hint.
        if (hintButton && hintText) {
            hintButton.addEventListener("click", () => {
                if (state.hintsUsed < 10) {
                    state.hintsUsed += 1;
                }

                hintText.removeAttribute("hidden");
            });
        }

        // Guided diagnosis fills the correct selections.
        if (guidedButton) {
            guidedButton.addEventListener("click", () => {
                state.guidedDiagnosisUsed = true;

                htmlIdSelect.value = CORRECT.html_id;
                jsSelectorSelect.value = CORRECT.js_selector;

                const setRadio = (name, value) => {
                    const target = form.querySelector(
                        `input[name="${name}"][value="${value}"]`
                    );

                    if (target) {
                        target.checked = true;
                    }
                };

                setRadio("fe_root_cause", CORRECT.root_cause);
                setRadio("fe_null_reason", CORRECT.null_reason);
                setRadio(
                    "fe_failure_mechanism",
                    CORRECT.failure_mechanism
                );

                if (statusText) {
                    statusText.textContent =
                        "Guided answers filled in. Run the " +
                        "diagnosis to confirm.";
                }
            });
        }

        // Run diagnosis.
        runButton.addEventListener("click", () => {
            state.diagnosisAttempts += 1;
            state.diagnosticRuns = state.diagnosisAttempts;

            if (selectionsAreCorrect()) {
                state.diagnosisConfirmed = true;

                if (statusText) {
                    statusText.textContent =
                        "Diagnosis confirmed: the selector id " +
                        "mismatch is the root cause.";
                    statusText.classList.add("fe-status--ok");
                    statusText.classList.remove("fe-status--bad");
                }
            } else {
                state.incorrectDiagnosisAttempts += 1;

                if (statusText) {
                    statusText.textContent =
                        "That combination is not correct yet. " +
                        "Review the evidence and try again.";
                    statusText.classList.add("fe-status--bad");
                    statusText.classList.remove("fe-status--ok");
                }
            }

            updateSubmitState();
        });

        // Finding + actions change submit readiness.
        findingInput.addEventListener("input", () => {
            if (findingValidation) {
                if (findingIsValid()) {
                    findingValidation.setAttribute("hidden", "");
                } else {
                    findingValidation.removeAttribute("hidden");
                }
            }

            updateSubmitState();
        });

        actionCheckboxes.forEach((box) => {
            box.addEventListener("change", updateSubmitState);
        });

        // Restore a previous answer when returning to this step.
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

            htmlIdSelect.value =
                saved.selected_html_id || "";
            jsSelectorSelect.value =
                saved.selected_js_selector || "";

            const setRadio = (name, value) => {
                if (!value) {
                    return;
                }

                const target = form.querySelector(
                    `input[name="${name}"][value="${value}"]`
                );

                if (target) {
                    target.checked = true;
                }
            };

            setRadio("fe_root_cause", saved.selected_root_cause);
            setRadio("fe_null_reason", saved.selected_null_reason);
            setRadio(
                "fe_failure_mechanism",
                saved.selected_failure_mechanism
            );

            if (Array.isArray(saved.investigation_actions)) {
                actionCheckboxes.forEach((box) => {
                    box.checked =
                        saved.investigation_actions.includes(
                            box.value
                        );
                });
            }

            findingInput.value = saved.technical_finding || "";

            state.diagnosisAttempts =
                saved.diagnosis_attempts || 0;
            state.incorrectDiagnosisAttempts =
                saved.incorrect_diagnosis_attempts || 0;
            state.diagnosticRuns =
                saved.diagnostic_runs ||
                state.diagnosisAttempts;
            state.hintsUsed = saved.hints_used || 0;
            state.guidedDiagnosisUsed = Boolean(
                saved.guided_diagnosis_used
            );
            state.diagnosisConfirmed = Boolean(
                saved.diagnosis_confirmed
            );

            updateSubmitState();
        }

        // Build the JSON payload on submit.
        form.addEventListener("submit", (event) => {
            if (
                !state.diagnosisConfirmed ||
                getSelectedActions().length !== 3 ||
                !findingIsValid()
            ) {
                event.preventDefault();
                updateSubmitState();
                return;
            }

            if (
                state.incorrectDiagnosisAttempts >
                state.diagnosisAttempts
            ) {
                state.incorrectDiagnosisAttempts =
                    state.diagnosisAttempts;
            }

            const payload = {
                task_type: "frontend_investigation",
                issue_id: "FE-4021",
                investigation_actions: getSelectedActions(),
                diagnosis_attempts: state.diagnosisAttempts,
                incorrect_diagnosis_attempts:
                    state.incorrectDiagnosisAttempts,
                diagnostic_runs: state.diagnosticRuns,
                selected_html_id: htmlIdSelect.value,
                selected_js_selector: jsSelectorSelect.value,
                selected_root_cause:
                    getSelectedRadio("fe_root_cause"),
                selected_null_reason:
                    getSelectedRadio("fe_null_reason"),
                selected_failure_mechanism: getSelectedRadio(
                    "fe_failure_mechanism"
                ),
                hints_used: state.hintsUsed,
                guided_diagnosis_used:
                    state.guidedDiagnosisUsed,
                diagnosis_confirmed: true,
                technical_finding:
                    findingInput.value.trim(),
            };

            hiddenAnswer.value = JSON.stringify(payload);
        });

        restoreSavedAnswer();
        updateSubmitState();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeFrontendInvestigation
        );
    } else {
        initializeFrontendInvestigation();
    }
})();