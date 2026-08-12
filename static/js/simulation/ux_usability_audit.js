function initUXUsabilityAudit() {
    const form = document.getElementById("ux-audit-form");
    const answerInput = document.getElementById("ux-audit-answer");

    if (!form || !answerInput) {
        console.error("UX Audit: form or answer input missing.");
        return;
    }

    const MAX_ISSUES = 5;

    const flaggedIssues = new Map();

    let usabilityTestRuns = 0;
    let lastTestResult = null;


    const ISSUE_LIBRARY = {
        back_icon: {
            label: "Ambiguous icon-only back control",
            correctCategory: "interaction_design",
            correctSeverity: "medium"
        },

        progress_state: {
            label: "Unclear checkout progress state",
            correctCategory: "information_architecture",
            correctSeverity: "medium"
        },

        card_label: {
            label: "Card-number field lacks a proper visible label",
            correctCategory: "accessibility",
            correctSeverity: "high"
        },

        error_color_only: {
            label: "Payment error relies too heavily on color",
            correctCategory: "accessibility",
            correctSeverity: "critical"
        },

        low_contrast: {
            label: "Legal text has insufficient contrast",
            correctCategory: "accessibility",
            correctSeverity: "high"
        },

        destructive_proximity: {
            label: "Destructive action competes with payment CTA",
            correctCategory: "visual_hierarchy",
            correctSeverity: "high"
        },

        tiny_touch_target: {
            label: "Help button has a tiny touch target",
            correctCategory: "accessibility",
            correctSeverity: "high"
        }
    };


    const issueCount = document.getElementById("ux-issue-count");
    const flaggedContainer = document.getElementById("ux-flagged-issues");

    const deviceButtons = document.querySelectorAll(".ux-device-btn");
    const prototype = document.getElementById("ux-checkout-prototype");

    const auditTargets = document.querySelectorAll(".ux-audit-target");

    const runTestButton = document.getElementById(
        "ux-run-usability-test"
    );

    const resultsPanel = document.getElementById(
        "ux-usability-results"
    );

    const completionRate = document.getElementById(
        "ux-completion-rate"
    );

    const checkoutTime = document.getElementById(
        "ux-checkout-time"
    );

    const criticalFailures = document.getElementById(
        "ux-critical-failures"
    );

    const observationList = document.getElementById(
        "ux-observation-list"
    );

    const statusBox = document.getElementById(
        "ux-audit-status"
    );

    const summaryInput = document.getElementById(
        "ux-audit-summary"
    );

    const submitButton = document.getElementById(
        "ux-audit-submit"
    );


    function setStatus(message, type = "") {
        if (!statusBox) {
            return;
        }

        statusBox.textContent = message;

        statusBox.classList.remove(
            "ux-status--success",
            "ux-status--warning",
            "ux-status--error"
        );

        if (type) {
            statusBox.classList.add(
                `ux-status--${type}`
            );
        }
    }


    function getReleaseDecision() {
        const selected = document.querySelector(
            'input[name="ux_release_decision"]:checked'
        );

        return selected ? selected.value : "";
    }


    function updateIssueCounter() {
        if (issueCount) {
            issueCount.textContent =
                `${flaggedIssues.size} / ${MAX_ISSUES}`;
        }
    }


    function updateAnswer() {
        const issues = [];

        flaggedIssues.forEach((issue, issueId) => {
            issues.push({
                issue_id: issueId,
                category: issue.category || "",
                severity: issue.severity || "",
                proposed_fix: issue.proposedFix || ""
            });
        });


        answerInput.value = JSON.stringify({
            task_type: "ux_usability_audit",
            issue_id: "UX-2048",

            flagged_issues: issues,

            usability_test_runs: usabilityTestRuns,

            usability_result: lastTestResult,

            release_decision: getReleaseDecision(),

            release_summary:
                summaryInput
                    ? summaryInput.value.trim()
                    : ""
        });
    }


    /* ==========================================
       MOBILE / DESKTOP
    ========================================== */

    deviceButtons.forEach((button) => {
        button.addEventListener("click", () => {

            deviceButtons.forEach((item) => {
                item.classList.remove("active");
            });

            button.classList.add("active");


            if (!prototype) {
                return;
            }

            prototype.classList.remove(
                "ux-checkout-prototype--mobile",
                "ux-checkout-prototype--desktop"
            );


            if (button.dataset.device === "desktop") {
                prototype.classList.add(
                    "ux-checkout-prototype--desktop"
                );
            } else {
                prototype.classList.add(
                    "ux-checkout-prototype--mobile"
                );
            }
        });
    });


    /* ==========================================
       RENDER FLAGGED ISSUES
    ========================================== */

    function renderFlaggedIssues() {
        if (!flaggedContainer) {
            return;
        }

        flaggedContainer.innerHTML = "";


        if (flaggedIssues.size === 0) {
            flaggedContainer.innerHTML = `
                <p class="ux-empty-audit">
                    No issues flagged yet.
                </p>
            `;

            updateIssueCounter();
            updateAnswer();

            return;
        }


        let number = 1;


        flaggedIssues.forEach((issue, issueId) => {
            const definition =
                ISSUE_LIBRARY[issueId];

            if (!definition) {
                return;
            }


            const card =
                document.createElement("article");

            card.className =
                "ux-flagged-issue";


            card.innerHTML = `
                <div class="ux-flagged-issue-heading">

                    <div>
                        <span class="ux-flagged-number">
                            Issue ${number}
                        </span>

                        <strong>
                            ${definition.label}
                        </strong>
                    </div>

                    <button
                        type="button"
                        class="ux-remove-flag"
                    >
                        ×
                    </button>

                </div>


                <div class="ux-audit-classification">

                    <div>
                        <label>
                            Category
                        </label>

                        <select class="ux-issue-category">

                            <option value="">
                                Choose category
                            </option>

                            <option value="accessibility">
                                Accessibility
                            </option>

                            <option value="usability">
                                Usability
                            </option>

                            <option value="interaction_design">
                                Interaction Design
                            </option>

                            <option value="information_architecture">
                                Information Architecture
                            </option>

                            <option value="visual_hierarchy">
                                Visual Hierarchy
                            </option>

                        </select>
                    </div>


                    <div>
                        <label>
                            Severity
                        </label>

                        <select class="ux-issue-severity">

                            <option value="">
                                Choose severity
                            </option>

                            <option value="low">
                                Low
                            </option>

                            <option value="medium">
                                Medium
                            </option>

                            <option value="high">
                                High
                            </option>

                            <option value="critical">
                                Critical
                            </option>

                        </select>
                    </div>

                </div>


                <div class="ux-audit-fix">

                    <label>
                        Proposed fix
                    </label>

                    <textarea
                        class="ux-issue-fix"
                        rows="3"
                        maxlength="500"
                        placeholder="Explain how you would fix this issue..."
                    ></textarea>

                </div>
            `;


            const category =
                card.querySelector(
                    ".ux-issue-category"
                );

            const severity =
                card.querySelector(
                    ".ux-issue-severity"
                );

            const fix =
                card.querySelector(
                    ".ux-issue-fix"
                );

            const remove =
                card.querySelector(
                    ".ux-remove-flag"
                );


            category.value =
                issue.category || "";

            severity.value =
                issue.severity || "";

            fix.value =
                issue.proposedFix || "";


            category.addEventListener(
                "change",
                () => {
                    issue.category =
                        category.value;

                    updateAnswer();
                }
            );


            severity.addEventListener(
                "change",
                () => {
                    issue.severity =
                        severity.value;

                    updateAnswer();
                }
            );


            fix.addEventListener(
                "input",
                () => {
                    issue.proposedFix =
                        fix.value.trim();

                    updateAnswer();
                }
            );


            remove.addEventListener(
                "click",
                () => {

                    flaggedIssues.delete(
                        issueId
                    );


                    const target =
                        document.querySelector(
                            `.ux-audit-target[data-issue-id="${issueId}"]`
                        );


                    if (target) {
                        target.classList.remove(
                            "ux-audit-target--flagged"
                        );
                    }


                    renderFlaggedIssues();
                }
            );


            flaggedContainer.appendChild(card);

            number += 1;
        });


        updateIssueCounter();
        updateAnswer();
    }


    /* ==========================================
       CLICK PROTOTYPE TO FLAG ISSUES
    ========================================== */

    auditTargets.forEach((target) => {

        target.addEventListener(
            "click",
            (event) => {

                event.preventDefault();
                event.stopPropagation();


                const issueId =
                    target.dataset.issueId;


                if (!issueId) {
                    return;
                }


                if (flaggedIssues.has(issueId)) {

                    flaggedIssues.delete(issueId);

                    target.classList.remove(
                        "ux-audit-target--flagged"
                    );

                    renderFlaggedIssues();

                    return;
                }


                if (
                    flaggedIssues.size >=
                    MAX_ISSUES
                ) {
                    setStatus(
                        "You already used all 5 issue flags. Remove one before selecting another.",
                        "warning"
                    );

                    return;
                }


                flaggedIssues.set(
                    issueId,
                    {
                        category: "",
                        severity: "",
                        proposedFix: ""
                    }
                );


                target.classList.add(
                    "ux-audit-target--flagged"
                );


                renderFlaggedIssues();


                setStatus(
                    `${flaggedIssues.size} of 5 issues flagged.`
                );
            }
        );
    });


    /* ==========================================
       AUDIT SCORING
    ========================================== */

    function calculateAuditScore() {
        let score = 0;


        flaggedIssues.forEach(
            (issue, issueId) => {

                const definition =
                    ISSUE_LIBRARY[issueId];


                if (!definition) {
                    return;
                }


                score += 10;


                if (
                    issue.category ===
                    definition.correctCategory
                ) {
                    score += 5;
                }


                if (
                    issue.severity ===
                    definition.correctSeverity
                ) {
                    score += 5;
                }


                if (
                    issue.proposedFix
                    && issue.proposedFix.length >= 20
                ) {
                    score += 5;
                }
            }
        );


        return Math.min(score, 100);
    }


    /* ==========================================
       USABILITY TEST
    ========================================== */

    if (runTestButton) {
        runTestButton.addEventListener("click", () => {
            usabilityTestRuns += 1;

            const score = calculateAuditScore();

            let completion = 62;
            let seconds = 255;
            let failures = 5;

            const observations = [];


            /* No / weak audit */

            if (flaggedIssues.size === 0) {
                observations.push(
                    "No UX issues were identified before testing."
                );
            }

            if (flaggedIssues.size < 3) {
                observations.push(
                    "The audit appears incomplete. Several usability risks were not investigated."
                );
            }


            /* Missing critical issues */

            if (!flaggedIssues.has("error_color_only")) {
                observations.push(
                    "4 of 10 users could not determine which payment field contained an error."
                );
            }

            if (!flaggedIssues.has("tiny_touch_target")) {
                observations.push(
                    "Mobile participants repeatedly missed the help control."
                );
            }

            if (!flaggedIssues.has("low_contrast")) {
                observations.push(
                    "Low-vision users had difficulty reading the legal and consent information."
                );
            }

            if (!flaggedIssues.has("destructive_proximity")) {
                observations.push(
                    "Several participants hesitated because Remove order competes with the Pay action."
                );
            }

            if (!flaggedIssues.has("card_label")) {
                observations.push(
                    "Assistive-technology users encountered unclear card-number field labeling."
                );
            }


            /* Score-based outcome */

            if (score >= 85) {
                completion = 96;
                seconds = 118;
                failures = 0;
            }

            else if (score >= 70) {
                completion = 89;
                seconds = 146;
                failures = 1;
            }

            else if (score >= 50) {
                completion = 79;
                seconds = 181;
                failures = 2;
            }

            else if (score >= 25) {
                completion = 70;
                seconds = 215;
                failures = 3;
            }


            if (observations.length === 0) {
                observations.push(
                    "Participants completed checkout successfully with no major usability breakdowns."
                );
            }


            lastTestResult = {
                audit_quality_score: score,
                task_completion_rate: completion,
                average_checkout_seconds: seconds,
                critical_failures: failures,
                observations: observations
            };


            if (completionRate) {
                completionRate.textContent =
                    `${completion}%`;
            }


            if (checkoutTime) {
                const minutes =
                    Math.floor(seconds / 60);

                const remainingSeconds =
                    seconds % 60;

                checkoutTime.textContent =
                    `${minutes}m ${remainingSeconds}s`;
            }


            if (criticalFailures) {
                criticalFailures.textContent =
                    String(failures);
            }


            if (observationList) {
                observationList.innerHTML = "";

                observations.forEach((text) => {
                    const item =
                        document.createElement("li");

                    item.textContent = text;

                    observationList.appendChild(item);
                });
            }


            if (resultsPanel) {
                resultsPanel.hidden = false;

                resultsPanel.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest"
                });
            }


            if (score >= 85) {
                setStatus(
                    "Excellent audit. The redesigned experience performed strongly in testing.",
                    "success"
                );
            }

            else if (score >= 60) {
                setStatus(
                    "The prototype improved, but some UX risks still need attention before release.",
                    "warning"
                );
            }

            else {
                setStatus(
                    "Testing exposed significant usability problems. Review your audit findings before making a release decision.",
                    "error"
                );
            }


            updateAnswer();
        });
    }


    /* ==========================================
       FINAL RESPONSE
    ========================================== */

    document
        .querySelectorAll(
            'input[name="ux_release_decision"]'
        )
        .forEach((radio) => {

            radio.addEventListener(
                "change",
                updateAnswer
            );
        });


    if (summaryInput) {
        summaryInput.addEventListener(
            "input",
            updateAnswer
        );
    }


    form.addEventListener(
        "submit",
        (event) => {

            const decision =
                getReleaseDecision();

            const summary =
                summaryInput
                    ? summaryInput.value.trim()
                    : "";


            if (flaggedIssues.size < 3) {
                event.preventDefault();

                setStatus(
                    "Flag at least 3 UX issues.",
                    "error"
                );

                return;
            }


            if (usabilityTestRuns < 1) {
                event.preventDefault();

                setStatus(
                    "Run the usability test before continuing.",
                    "error"
                );

                return;
            }


            if (!decision) {
                event.preventDefault();

                setStatus(
                    "Choose Ship, Iterate, or Block Release.",
                    "error"
                );

                return;
            }


            if (summary.length < 40) {
                event.preventDefault();

                setStatus(
                    "Explain your release decision in more detail.",
                    "error"
                );

                return;
            }


            updateAnswer();


            if (submitButton) {
                submitButton.disabled = true;

                submitButton.textContent =
                    "Saving audit...";
            }
        }
    );


    renderFlaggedIssues();
}


/* Reliable initialization */
if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initUXUsabilityAudit
    );
} else {
    initUXUsabilityAudit();
}