(() => {
    "use strict";

    const REQUIRED_TESTS = [
        "correct_selector",
        "safe_initialization",
        "existence_check",
        "handler_attached",
    ];

    const GUIDED_SOLUTION =
        "document.addEventListener('DOMContentLoaded', " +
        "function () {\n" +
        "    const buyNowButton = " +
        "document.getElementById('buy-now-btn');\n\n" +
        "    if (buyNowButton) {\n" +
        "        buyNowButton.addEventListener('click', " +
        "openCheckoutPanel);\n" +
        "    }\n" +
        "});";

    function analyzeCode(code) {
        const referencesCorrectId =
            /getElementById\s*\(\s*["']buy-now-btn["']\s*\)/.test(
                code
            ) ||
            /querySelector\s*\(\s*["']#buy-now-btn["']\s*\)/.test(
                code
            );

        const stillUsesWrongSelector =
            /getElementById\s*\(\s*["']checkout-btn["']\s*\)/.test(
                code
            ) ||
            /querySelector\s*\(\s*["']#checkout-btn["']\s*\)/.test(
                code
            );

        const usesDomReady =
            /DOMContentLoaded/.test(code) ||
            /\bdefer\b/.test(code) ||
            /window\s*\.\s*onload/.test(code);

        const hasExistenceCheck =
            /if\s*\(\s*[\w$]+\s*\)/.test(code) ||
            /[\w$]+\s*!==?\s*null/.test(code) ||
            /[\w$]+\s*&&/.test(code);

        const attachesClickHandler =
            /addEventListener\s*\(\s*["']click["']/.test(code);

        return {
            correct_selector:
                referencesCorrectId && !stillUsesWrongSelector,
            safe_initialization: usesDomReady,
            existence_check: hasExistenceCheck,
            handler_attached: attachesClickHandler,
        };
    }

    function initializeFrontendCodeLab() {
        const form = document.getElementById(
            "frontend-code-lab-form"
        );

        if (!form) {
            return;
        }

        const hiddenAnswer = document.getElementById("answer");
        const editor = document.getElementById("fe-code-editor");
        const initialCodeHolder =
            document.getElementById("fe-initial-code");
        const resetButton =
            document.getElementById("fe-code-reset");
        const hintButton =
            document.getElementById("fe-code-hint");
        const hintText =
            document.getElementById("fe-code-hint-text");
        const guidedButton =
            document.getElementById("fe-guided-fix");
        const guidedText =
            document.getElementById("fe-guided-fix-text");
        const runButton =
            document.getElementById("fe-run-tests");
        const statusText =
            document.getElementById("fe-tests-status");

        if (!hiddenAnswer || !editor) {
            return;
        }

        const testItems = Array.from(
            document.querySelectorAll(".fe-test-item")
        );

        const initialCode = initialCodeHolder
            ? initialCodeHolder.textContent
            : editor.value;

        const state = {
            testRuns: 0,
            failedTestRuns: 0,
            hintsUsed: 0,
            guidedFixUsed: false,
            passedTests: [],
        };

        function markTestItem(testId, passed) {
            const item = testItems.find(
                (node) =>
                    node.getAttribute("data-test-id") === testId
            );

            if (!item) {
                return;
            }

            const stateIcon = item.querySelector(".fe-test-state");

            item.classList.toggle("fe-test-item--pass", passed);
            item.classList.toggle("fe-test-item--fail", !passed);

            if (stateIcon) {
                stateIcon.textContent = passed ? "✓" : "✗";
            }
        }

        function runTests() {
            state.testRuns += 1;

            const results = analyzeCode(editor.value);

            const passedTests = REQUIRED_TESTS.filter(
                (testId) => results[testId]
            );

            REQUIRED_TESTS.forEach((testId) => {
                markTestItem(testId, Boolean(results[testId]));
            });

            const allPassed =
                passedTests.length === REQUIRED_TESTS.length;

            if (!allPassed) {
                state.failedTestRuns += 1;
            }

            state.passedTests = passedTests;

            if (statusText) {
                statusText.textContent = allPassed
                    ? "All checks passed. You can continue."
                    : "Some checks still fail. You can keep " +
                      "editing or continue anyway.";
                statusText.classList.toggle(
                    "fe-status--ok",
                    allPassed
                );
                statusText.classList.toggle(
                    "fe-status--bad",
                    !allPassed
                );
            }
        }

        if (runButton) {
            runButton.addEventListener("click", runTests);
        }

        if (resetButton) {
            resetButton.addEventListener("click", () => {
                editor.value = initialCode;

                testItems.forEach((item) => {
                    item.classList.remove(
                        "fe-test-item--pass",
                        "fe-test-item--fail"
                    );

                    const icon =
                        item.querySelector(".fe-test-state");

                    if (icon) {
                        icon.textContent = "•";
                    }
                });

                state.passedTests = [];

                if (statusText) {
                    statusText.textContent =
                        "Run the tests after editing the code.";
                    statusText.classList.remove(
                        "fe-status--ok",
                        "fe-status--bad"
                    );
                }
            });
        }

        if (hintButton && hintText) {
            hintButton.addEventListener("click", () => {
                if (state.hintsUsed < 100) {
                    state.hintsUsed += 1;
                }

                hintText.removeAttribute("hidden");
            });
        }

        if (guidedButton) {
            guidedButton.addEventListener("click", () => {
                state.guidedFixUsed = true;

                editor.value = GUIDED_SOLUTION;

                if (guidedText) {
                    guidedText.removeAttribute("hidden");
                    guidedText.setAttribute("open", "");
                }
            });
        }

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

            if (typeof saved.submitted_code === "string") {
                editor.value = saved.submitted_code;
            }

            state.testRuns = saved.test_runs || 0;
            state.failedTestRuns = saved.failed_test_runs || 0;
            state.hintsUsed = saved.hints_used || 0;
            state.guidedFixUsed = Boolean(saved.guided_fix_used);
        }

        form.addEventListener("submit", () => {
            const results = analyzeCode(editor.value);
            const passedTests = REQUIRED_TESTS.filter(
                (testId) => results[testId]
            );

            const payload = {
                task_type: "frontend_code_lab",
                issue_id: "FE-4021",
                submitted_code: editor.value.trim(),
                test_runs: state.testRuns,
                failed_test_runs: state.failedTestRuns,
                passed_tests: passedTests,
                hints_used: state.hintsUsed,
                guided_fix_used: state.guidedFixUsed,
            };

            hiddenAnswer.value = JSON.stringify(payload);
        });

        restoreSavedAnswer();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeFrontendCodeLab
        );
    } else {
        initializeFrontendCodeLab();
    }
})();