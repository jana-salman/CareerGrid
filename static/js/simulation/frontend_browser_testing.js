(() => {
    "use strict";

    const REQUIRED_TEST_IDS = [
        "desktop_mouse",
        "mobile_viewport",
        "keyboard_accessibility",
    ];

    const OUTCOME_TEXT = {
        desktop_mouse:
            "Clicking Buy Now opened the checkout panel.",
        mobile_viewport:
            "The button stayed visible and usable at 375px.",
        keyboard_accessibility:
            "The button was focusable and activated with the " +
            "keyboard; accessibility state updated.",
    };

    function initializeFrontendBrowserTesting() {
        const form = document.getElementById(
            "frontend-browser-testing-form"
        );

        if (!form) {
            return;
        }

        const hiddenAnswer = document.getElementById("answer");
        const statusText =
            document.getElementById("fe-testing-status");
        const releaseRadio = form.querySelector(
            'input[name="fe_release_decision"]'
        );
        const submitButton =
            document.getElementById("fe-testing-submit");

        if (
            !hiddenAnswer ||
            !releaseRadio ||
            !submitButton
        ) {
            return;
        }

        const cards = Array.from(
            document.querySelectorAll(".fe-test-card")
        );

        const passedTests = new Set();

        const state = {
            testCount: 0,
        };

        function allTestsPassed() {
            return REQUIRED_TEST_IDS.every((testId) =>
                passedTests.has(testId)
            );
        }

        function updateSubmitState() {
            const ready =
                allTestsPassed() && releaseRadio.checked;

            submitButton.disabled = !ready;
        }

        function markCard(card, testId) {
            const badge = card.querySelector(".fe-test-badge");
            const outcome =
                card.querySelector(".fe-test-outcome");

            if (badge) {
                badge.textContent = "Passed";
                badge.setAttribute("data-state", "pass");
            }

            if (outcome) {
                outcome.textContent =
                    OUTCOME_TEXT[testId] || "Passed.";
            }

            card.classList.add("fe-test-card--pass");
        }

        cards.forEach((card) => {
            const testId = card.getAttribute("data-test-id");
            const runButton =
                card.querySelector(".fe-run-test");

            if (!runButton || !testId) {
                return;
            }

            runButton.addEventListener("click", () => {
                state.testCount += 1;
                passedTests.add(testId);
                markCard(card, testId);

                if (allTestsPassed()) {
                    releaseRadio.disabled = false;

                    if (statusText) {
                        statusText.textContent =
                            "All required tests passed. Select " +
                            "the release decision to continue.";
                        statusText.classList.add(
                            "fe-status--ok"
                        );
                    }
                }

                updateSubmitState();
            });
        });

        releaseRadio.addEventListener("change", updateSubmitState);

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

            state.testCount =
                saved.test_count || 0;

            if (Array.isArray(saved.tests_run)) {
                saved.tests_run.forEach((test) => {
                    if (
                        test &&
                        test.passed &&
                        REQUIRED_TEST_IDS.includes(test.test_id)
                    ) {
                        passedTests.add(test.test_id);

                        const card = cards.find(
                            (node) =>
                                node.getAttribute(
                                    "data-test-id"
                                ) === test.test_id
                        );

                        if (card) {
                            markCard(card, test.test_id);
                        }
                    }
                });
            }

            if (allTestsPassed()) {
                releaseRadio.disabled = false;

                if (
                    saved.release_decision ===
                    "ready_for_release"
                ) {
                    releaseRadio.checked = true;
                }
            }

            updateSubmitState();
        }

        form.addEventListener("submit", (event) => {
            if (!allTestsPassed() || !releaseRadio.checked) {
                event.preventDefault();
                updateSubmitState();
                return;
            }

            const testCount = Math.max(
                REQUIRED_TEST_IDS.length,
                state.testCount
            );

            const payload = {
                task_type: "frontend_browser_testing",
                target: {
                    component: "buy_now_button",
                    page: "product_page",
                },
                tests_run: REQUIRED_TEST_IDS.map((testId) => ({
                    test_id: testId,
                    expected_outcome: "pass",
                    actual_outcome: "pass",
                    passed: true,
                })),
                test_count: testCount,
                all_tests_passed: true,
                release_decision: "ready_for_release",
            };

            hiddenAnswer.value = JSON.stringify(payload);
        });

        restoreSavedAnswer();
        updateSubmitState();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeFrontendBrowserTesting
        );
    } else {
        initializeFrontendBrowserTesting();
    }
})();
