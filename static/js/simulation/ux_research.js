document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ux-research-form");
    const answerInput = document.getElementById("ux-research-answer");

    if (!form || !answerInput) {
        return;
    }

    const evidenceButtons = document.querySelectorAll(
        ".ux-evidence-toggle"
    );

    const actionCheckboxes = document.querySelectorAll(
        ".ux-action-checkbox"
    );

    const problemRadios = document.querySelectorAll(
        'input[name="ux_primary_problem"]'
    );

    const evidenceCheckboxes = document.querySelectorAll(
        ".ux-supporting-evidence"
    );

    const findingInput = document.getElementById(
        "ux-research-finding"
    );

    const findingValidation = document.getElementById(
        "ux-finding-validation"
    );

    const runDiagnosisButton = document.getElementById(
        "ux-run-diagnosis"
    );

    const diagnosisStatus = document.getElementById(
        "ux-diagnosis-status"
    );

    const hintButton = document.getElementById(
        "ux-research-hint"
    );

    const hintBox = document.getElementById(
        "ux-research-hint-box"
    );

    const submitButton = document.getElementById(
        "ux-research-submit"
    );


    const openedEvidence = new Set();

    let investigationAttempts = 0;
    let hintsUsed = 0;


    // -----------------------------------------------------
    // Helpers
    // -----------------------------------------------------

    function getSelectedProblem() {
        const selected = document.querySelector(
            'input[name="ux_primary_problem"]:checked'
        );

        return selected ? selected.value : "";
    }


    function getSelectedEvidence() {
        return Array.from(evidenceCheckboxes)
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.value);
    }


    function getCompletedActions() {
        return Array.from(actionCheckboxes)
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.value);
    }


    function buildResponse() {
        return {
            task_type: "ux_research",
            issue_id: "UX-2048",

            opened_evidence: Array.from(openedEvidence),

            selected_problem: getSelectedProblem(),

            selected_evidence: getSelectedEvidence(),

            research_finding: findingInput
                ? findingInput.value.trim()
                : "",

            investigation_attempts: investigationAttempts,

            hints_used: hintsUsed
        };
    }


    function updateHiddenAnswer() {
        answerInput.value = JSON.stringify(
            buildResponse()
        );
    }


    function setDiagnosisMessage(
        message,
        status = "neutral"
    ) {
        if (!diagnosisStatus) {
            return;
        }

        diagnosisStatus.textContent = message;

        diagnosisStatus.classList.remove(
            "ux-status--success",
            "ux-status--warning",
            "ux-status--error"
        );

        if (status === "success") {
            diagnosisStatus.classList.add(
                "ux-status--success"
            );
        }

        if (status === "warning") {
            diagnosisStatus.classList.add(
                "ux-status--warning"
            );
        }

        if (status === "error") {
            diagnosisStatus.classList.add(
                "ux-status--error"
            );
        }
    }


    // -----------------------------------------------------
    // Evidence accordion
    // -----------------------------------------------------

    evidenceButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const evidenceId =
                button.dataset.evidenceId;

            const evidenceBody =
                button.parentElement.querySelector(
                    ".ux-evidence-body"
                );

            if (!evidenceBody) {
                return;
            }

            const isCurrentlyOpen =
                !evidenceBody.hidden;


            // Close the other evidence panels.
            document
                .querySelectorAll(".ux-evidence-body")
                .forEach((body) => {
                    body.hidden = true;
                });

            evidenceButtons.forEach(
                (otherButton) => {
                    otherButton.setAttribute(
                        "aria-expanded",
                        "false"
                    );

                    otherButton.classList.remove(
                        "active"
                    );
                }
            );


            // Open the selected panel unless the user
            // clicked an already-open panel.
            if (!isCurrentlyOpen) {
                evidenceBody.hidden = false;

                button.setAttribute(
                    "aria-expanded",
                    "true"
                );

                button.classList.add("active");

                openedEvidence.add(evidenceId);

                investigationAttempts += 1;
            }

            updateHiddenAnswer();
        });
    });


    // -----------------------------------------------------
    // Diagnosis
    // -----------------------------------------------------

    if (runDiagnosisButton) {
        runDiagnosisButton.addEventListener(
            "click",
            () => {
                investigationAttempts += 1;

                const selectedProblem =
                    getSelectedProblem();

                const selectedEvidence =
                    getSelectedEvidence();

                const completedActions =
                    getCompletedActions();


                if (openedEvidence.size < 3) {
                    setDiagnosisMessage(
                        "Review at least three research sources before running your diagnosis.",
                        "warning"
                    );

                    updateHiddenAnswer();
                    return;
                }


                if (completedActions.length < 2) {
                    setDiagnosisMessage(
                        "Complete at least two investigation actions first.",
                        "warning"
                    );

                    updateHiddenAnswer();
                    return;
                }


                if (!selectedProblem) {
                    setDiagnosisMessage(
                        "Choose the primary checkout problem.",
                        "warning"
                    );

                    updateHiddenAnswer();
                    return;
                }


                if (selectedEvidence.length < 2) {
                    setDiagnosisMessage(
                        "Select at least two pieces of supporting evidence.",
                        "warning"
                    );

                    updateHiddenAnswer();
                    return;
                }


                if (
                    selectedProblem ===
                    "forced_account_creation"
                ) {
                    setDiagnosisMessage(
                        "Your diagnosis is well supported. The evidence consistently points to mandatory account creation as the main checkout friction.",
                        "success"
                    );
                } else {
                    setDiagnosisMessage(
                        "Your diagnosis does not strongly match the evidence. Review the funnel drop-off, user interview, usability test, and support feedback again.",
                        "warning"
                    );
                }

                updateHiddenAnswer();
            }
        );
    }


    // -----------------------------------------------------
    // Hint
    // -----------------------------------------------------

    if (hintButton && hintBox) {
        hintButton.addEventListener("click", () => {
            hintsUsed += 1;

            hintBox.hidden = !hintBox.hidden;

            hintButton.textContent =
                hintBox.hidden
                    ? "Show a hint"
                    : "Hide hint";

            updateHiddenAnswer();
        });
    }


    // -----------------------------------------------------
    // Keep answer updated
    // -----------------------------------------------------

    problemRadios.forEach((radio) => {
        radio.addEventListener(
            "change",
            updateHiddenAnswer
        );
    });


    evidenceCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener(
            "change",
            updateHiddenAnswer
        );
    });


    actionCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener(
            "change",
            updateHiddenAnswer
        );
    });


    if (findingInput) {
        findingInput.addEventListener(
            "input",
            () => {
                if (
                    findingValidation
                    && findingInput.value.trim().length >= 20
                ) {
                    findingValidation.hidden = true;
                }

                updateHiddenAnswer();
            }
        );
    }


    // -----------------------------------------------------
    // Restore Previous Step response
    // -----------------------------------------------------

    function restoreSavedAnswer() {
        const savedValue =
            answerInput.dataset.savedAnswer;

        if (!savedValue) {
            updateHiddenAnswer();
            return;
        }

        try {
            const saved = JSON.parse(savedValue);


            if (
                Array.isArray(
                    saved.opened_evidence
                )
            ) {
                saved.opened_evidence.forEach(
                    (evidenceId) => {
                        openedEvidence.add(
                            evidenceId
                        );
                    }
                );
            }


            if (saved.selected_problem) {
                const savedRadio =
                    document.querySelector(
                        `input[name="ux_primary_problem"][value="${saved.selected_problem}"]`
                    );

                if (savedRadio) {
                    savedRadio.checked = true;
                }
            }


            if (
                Array.isArray(
                    saved.selected_evidence
                )
            ) {
                evidenceCheckboxes.forEach(
                    (checkbox) => {
                        checkbox.checked =
                            saved.selected_evidence.includes(
                                checkbox.value
                            );
                    }
                );
            }


            if (
                findingInput
                && saved.research_finding
            ) {
                findingInput.value =
                    saved.research_finding;
            }


            investigationAttempts =
                Number(
                    saved.investigation_attempts || 0
                );

            hintsUsed =
                Number(saved.hints_used || 0);


            updateHiddenAnswer();

        } catch (error) {
            console.warn(
                "Could not restore the saved UX research response.",
                error
            );

            updateHiddenAnswer();
        }
    }


    // -----------------------------------------------------
    // Final submission validation
    // -----------------------------------------------------

    form.addEventListener("submit", (event) => {
        const selectedProblem =
            getSelectedProblem();

        const selectedEvidence =
            getSelectedEvidence();

        const completedActions =
            getCompletedActions();

        const finding =
            findingInput
                ? findingInput.value.trim()
                : "";


        if (openedEvidence.size < 3) {
            event.preventDefault();

            setDiagnosisMessage(
                "Open and review at least three research sources before continuing.",
                "error"
            );

            return;
        }


        if (completedActions.length < 2) {
            event.preventDefault();

            setDiagnosisMessage(
                "Complete at least two investigation actions before continuing.",
                "error"
            );

            return;
        }


        if (!selectedProblem) {
            event.preventDefault();

            setDiagnosisMessage(
                "Choose the primary UX problem before continuing.",
                "error"
            );

            return;
        }


        if (selectedEvidence.length < 2) {
            event.preventDefault();

            setDiagnosisMessage(
                "Select at least two pieces of supporting evidence.",
                "error"
            );

            return;
        }


        if (finding.length < 20) {
            event.preventDefault();

            if (findingValidation) {
                findingValidation.hidden = false;
            }

            if (findingInput) {
                findingInput.focus();
            }

            return;
        }


        updateHiddenAnswer();

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent =
                "Saving investigation...";
        }
    });


    restoreSavedAnswer();
});