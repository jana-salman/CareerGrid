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

        if (!hiddenAnswer) {
            return;
        }

        const cards = Array.from(
            document.querySelectorAll(".fe-test-card")
        );

        const passedTests = new Set();

        const state = {
            testCount: 0,
        };

        function releaseDecision() {
            const selected = form.querySelector(
                'input[name="fe_release_decision"]:checked'
            );

            // Default keeps the user moving if nothing is chosen.
            return selected ? selected.value : "needs_more_work";
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

                if (statusText) {
                    const remaining = REQUIRED_TEST_IDS.filter(
                        (id) => !passedTests.has(id)
                    );

                    statusText.textContent =
                        remaining.length === 0
                            ? "All three tests passed. Choose a " +
                              "release decision and continue."
                            : "Test recorded. You can run the " +
                              "remaining tests or continue.";

                    statusText.classList.toggle(
                        "fe-status--ok",
                        remaining.length === 0
                    );
                }
            });
        });

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

            state.testCount = saved.test_count || 0;

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

            if (saved.release_decision) {
                const radio = form.querySelector(
                    'input[name="fe_release_decision"]' +
                        `[value="${saved.release_decision}"]`
                );

                if (radio) {
                    radio.checked = true;
                }
            }
        }

        form.addEventListener("submit", () => {
            const testsRun = Array.from(passedTests).map(
                (testId) => ({
                    test_id: testId,
                    expected_outcome: "pass",
                    actual_outcome: "pass",
                    passed: true,
                })
            );

            const testCount = Math.max(
                state.testCount,
                testsRun.length
            );

            const payload = {
                task_type: "frontend_browser_testing",
                target: {
                    component: "buy_now_button",
                    page: "product_page",
                },
                tests_run: testsRun,
                test_count: testCount,
                all_tests_passed:
                    testsRun.length === REQUIRED_TEST_IDS.length,
                release_decision: releaseDecision(),
            };

            hiddenAnswer.value = JSON.stringify(payload);
        });

        restoreSavedAnswer();
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