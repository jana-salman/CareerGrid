function initUIQualityAssurance() {
    const form = document.getElementById("ui-qa-form");
    const answerInput = document.getElementById("ui-qa-answer");

    if (!form || !answerInput) return;

    const checks = new Set();
    let decision = "";

    const checkButtons =
        document.querySelectorAll(".ui-qa-check");

    const decisionButtons =
        document.querySelectorAll(".ui-qa-decision");

    const deviceButtons =
        document.querySelectorAll(".ui-qa-device");

    const preview =
        document.getElementById("ui-qa-preview");

    const count =
        document.getElementById("ui-qa-count");

    const notes =
        document.getElementById("ui-qa-notes");

    const charCount =
        document.getElementById("ui-qa-char-count");

    const status =
        document.getElementById("ui-qa-status");


    function updateAnswer() {
        answerInput.value = JSON.stringify({
            task_type: "ui_quality_assurance",
            issue_id: "UI-4108",
            completed_checks: Array.from(checks),
            handoff_decision: decision,
            notes: notes ? notes.value.trim() : ""
        });
    }


    // ==========================================
    // QA CHECK BUTTONS
    // ==========================================

    checkButtons.forEach(button => {

        button.addEventListener("click", () => {

            const check = button.dataset.check;

            if (!check) return;

            const icon =
                button.querySelector(
                    ".ui-qa-check-icon"
                );

            const result =
                button.querySelector(
                    ".ui-qa-result"
                );


            if (checks.has(check)) {

                checks.delete(check);

                button.classList.remove(
                    "completed"
                );

                if (icon) {
                    icon.textContent = "□";
                }

                if (result) {
                    result.textContent =
                        "Not checked";
                }

            } else {

                checks.add(check);

                button.classList.add(
                    "completed"
                );

                if (icon) {
                    icon.textContent = "✓";
                }

                if (result) {
                    result.textContent =
                        "Passed";
                }
            }


            if (count) {
                count.textContent =
                    `${checks.size} / 6`;
            }

            if (status) {
                status.textContent =
                    checks.size === 6
                        ? "All UI quality checks completed."
                        : `${checks.size} of 6 QA checks completed.`;

                status.classList.remove(
                    "ui-qa-status--error"
                );
            }

            updateAnswer();
        });
    });


    // ==========================================
    // HANDOFF DECISION
    // ==========================================

    decisionButtons.forEach(button => {

        button.addEventListener("click", () => {

            decisionButtons.forEach(item => {
                item.classList.remove("active");
            });

            button.classList.add("active");

            decision =
                button.dataset.decision || "";

            updateAnswer();
        });
    });


    // ==========================================
    // DESKTOP / TABLET / MOBILE
    // ==========================================

    deviceButtons.forEach(button => {

        button.addEventListener("click", () => {

            deviceButtons.forEach(item => {
                item.classList.remove("active");
            });

            button.classList.add("active");

            if (!preview) return;

            preview.classList.remove(
                "ui-qa-preview--desktop",
                "ui-qa-preview--tablet",
                "ui-qa-preview--mobile"
            );

            const device =
                button.dataset.device || "desktop";

            preview.classList.add(
                `ui-qa-preview--${device}`
            );
        });
    });


    // ==========================================
    // NOTES
    // ==========================================

    if (notes) {

        notes.addEventListener("input", () => {

            if (charCount) {
                charCount.textContent =
                    `${notes.value.length} characters`;
            }

            updateAnswer();
        });
    }


    // ==========================================
    // SUBMIT VALIDATION
    // ==========================================

    form.addEventListener("submit", event => {

        if (checks.size !== 6) {

            event.preventDefault();

            if (status) {
                status.textContent =
                    "Complete all 6 UI quality checks before continuing.";

                status.classList.add(
                    "ui-qa-status--error"
                );
            }

            return;
        }


        if (!decision) {

            event.preventDefault();

            if (status) {
                status.textContent =
                    "Choose a handoff decision before continuing.";

                status.classList.add(
                    "ui-qa-status--error"
                );
            }

            return;
        }


        const notesText =
            notes
                ? notes.value.trim()
                : "";

        if (notesText.length < 80) {

            event.preventDefault();

            if (status) {
                status.textContent =
                    "Write at least 80 characters of QA handoff notes.";

                status.classList.add(
                    "ui-qa-status--error"
                );
            }

            if (notes) {
                notes.focus();
            }

            return;
        }

        updateAnswer();
    });


    updateAnswer();
}


if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initUIQualityAssurance
    );

} else {

    initUIQualityAssurance();
}