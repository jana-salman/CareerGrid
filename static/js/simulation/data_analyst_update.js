document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("dataAnalystUpdateForm");

    if (!form) {
        return;
    }

    const subject = document.getElementById("updateSubject");
    const executiveUpdate = document.getElementById("executiveUpdate");
    const recommendation = document.getElementById("updateRecommendation");

    const subjectCount = document.getElementById("subjectCount");
    const updateCount = document.getElementById("updateCount");

    const finishButton = document.getElementById("finishDataAnalystBtn");
    const errorBox = document.getElementById("updateError");

    const checkSubject = document.getElementById("checkSubject");
    const checkCause = document.getElementById("checkCause");
    const checkRevenue = document.getElementById("checkRevenue");
    const checkRecommendation = document.getElementById("checkRecommendation");
    const checkMessage = document.getElementById("checkMessage");

    function getSelected(name) {
        return form.querySelector(`input[name="${name}"]:checked`);
    }

    function updateRadioCards(name, selector) {
        const radios = form.querySelectorAll(`input[name="${name}"]`);

        radios.forEach(function (radio) {
            const card = radio.closest(selector);

            if (!card) {
                return;
            }

            card.classList.toggle("is-selected", radio.checked);
        });
    }

    function setChecklist(element, complete, label) {
        if (!element) {
            return;
        }

        element.classList.toggle("is-complete", complete);
        element.textContent = complete
            ? `✓ ${label}`
            : `○ ${label}`;
    }

    function validateReadiness() {
        const hasSubject =
            subject.value.trim().length >= 8;

        const hasCause =
            Boolean(getSelected("root_cause"));

        const hasRevenue =
            Boolean(getSelected("verified_revenue"));

        const hasRecommendation =
            recommendation.value !== "";

        const hasMessage =
            executiveUpdate.value.trim().length >= 80;

        setChecklist(
            checkSubject,
            hasSubject,
            "Subject"
        );

        setChecklist(
            checkCause,
            hasCause,
            "Root cause"
        );

        setChecklist(
            checkRevenue,
            hasRevenue,
            "KPI"
        );

        setChecklist(
            checkRecommendation,
            hasRecommendation,
            "Recommendation"
        );

        setChecklist(
            checkMessage,
            hasMessage,
            "Executive update"
        );

        const ready =
            hasSubject &&
            hasCause &&
            hasRevenue &&
            hasRecommendation &&
            hasMessage;

        finishButton.disabled = !ready;

        return ready;
    }

    subject.addEventListener("input", function () {
        subjectCount.textContent =
            `${subject.value.length} / 100`;

        validateReadiness();
    });

    executiveUpdate.addEventListener(
        "input",
        function () {
            updateCount.textContent =
                `${executiveUpdate.value.length} / 900`;

            validateReadiness();
        }
    );

    recommendation.addEventListener(
        "change",
        validateReadiness
    );

    form
        .querySelectorAll('input[name="root_cause"]')
        .forEach(function (radio) {
            radio.addEventListener(
                "change",
                function () {
                    updateRadioCards(
                        "root_cause",
                        ".da-choice-card"
                    );

                    validateReadiness();
                }
            );
        });

    form
        .querySelectorAll(
            'input[name="verified_revenue"]'
        )
        .forEach(function (radio) {
            radio.addEventListener(
                "change",
                function () {
                    updateRadioCards(
                        "verified_revenue",
                        ".da-kpi-choice"
                    );

                    validateReadiness();
                }
            );
        });

    form.addEventListener("submit", function (event) {
        /*
         * app.py expects ONE field called "answer".
         * The interactive Step 5 interface therefore gets
         * converted into structured JSON before submission.
         */

        event.preventDefault();

        errorBox.style.display = "none";
        errorBox.textContent = "";

        if (!validateReadiness()) {
            errorBox.textContent =
                "Complete all five parts of the leadership update before finishing the simulation.";

            errorBox.style.display = "block";

            errorBox.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

            return;
        }

        const selectedCause =
            getSelected("root_cause");

        const selectedRevenue =
            getSelected("verified_revenue");

        const response = {
            task_type: "data_analyst_final_update",
            issue_id: "DA-2104",

            subject:
                subject.value.trim(),

            root_cause:
                selectedCause.value,

            verified_revenue:
                selectedRevenue.value,

            recommendation:
                recommendation.value,

            executive_update:
                executiveUpdate.value.trim()
        };

        let answerInput =
            form.querySelector(
                'input[name="answer"]'
            );

        if (!answerInput) {
            answerInput =
                document.createElement("input");

            answerInput.type = "hidden";
            answerInput.name = "answer";

            form.appendChild(answerInput);
        }

        answerInput.value =
            JSON.stringify(response);

        finishButton.disabled = true;
        finishButton.textContent =
            "Evaluating...";

        form.submit();
    });

    subjectCount.textContent =
        `${subject.value.length} / 100`;

    updateCount.textContent =
        `${executiveUpdate.value.length} / 900`;

    updateRadioCards(
        "root_cause",
        ".da-choice-card"
    );

    updateRadioCards(
        "verified_revenue",
        ".da-kpi-choice"
    );

    validateReadiness();
});