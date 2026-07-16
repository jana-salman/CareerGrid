(() => {
"use strict";

function initializeCodeLab() {
    const form = document.getElementById(
        "code-lab-task-form"
    );

    // Stop safely on simulation steps without the Code Lab.
    if (!form) {
        return;
    }

    const hiddenAnswer =
        document.getElementById("answer");

    const codeEditor =
        document.getElementById("submitted-code");

    const lineNumbers =
        document.getElementById("editor-line-numbers");

    const resetButton =
        document.getElementById("reset-code-button");

    const hintButton =
        document.getElementById("show-hint-button");

    const hintBox =
        document.getElementById("code-hint");

    const runTestsButton =
        document.getElementById("run-tests-button");

    const testOutput =
        document.getElementById("test-output");

    const testRunCounter =
        document.getElementById("test-run-counter");

    const workspaceStatus =
        document.getElementById("code-lab-status");

    const workspaceStatusText =
        document.getElementById(
            "code-lab-status-text"
        );

    const submitButton =
        document.getElementById(
            "submit-code-lab-button"
        );
    const guidedFixPanel =
    document.getElementById(
        "guided-fix-panel"
    );

    const applyGuidedFixButton =
    document.getElementById(
        "apply-guided-fix-button"
    );

    if (
        !hiddenAnswer ||
        !codeEditor ||
        !runTestsButton ||
        !testOutput ||
        !submitButton
    ) {
        console.error(
            "CareerGrid Code Lab could not start because required elements are missing."
        );

        return;
    }

    const initialCode = codeEditor.value;

    const requiredTestIds = [
        "valid_cart",
        "missing_product_id",
        "no_server_crash"
    ];

    let testRuns = 0;
let failedTestRuns = 0;
let hintsUsed = 0;
let hintWasCounted = false;
let guidedFixUsed = false;
let passedTests = [];
let lastTestedCode = null;

const guidedSolution = `def create_order(cart_items):
    order_items = []

    for item in cart_items:
        product_id = item.get("product_id")

        if not product_id:
            return {
                "error": "product_id is required"
            }, 400

        order_items.append(
            create_order_item(product_id)
        )

    return {"status": "created"}, 201`;

    function updateLineNumbers() {
        if (!lineNumbers) {
            return;
        }

        const numberOfLines =
            codeEditor.value.split("\n").length;

        lineNumbers.innerHTML = Array.from(
            { length: numberOfLines },
            (_, index) => index + 1
        ).join("<br>");
    }

    function updateRunCounter() {
        if (testRunCounter) {
            testRunCounter.textContent =
                `Runs: ${testRuns}`;
        }
    }

    function updateWorkspaceStatus(
        status,
        message
    ) {
        if (!workspaceStatus) {
            return;
        }

        workspaceStatus.classList.remove(
            "tests-passed",
            "tests-failed"
        );

        if (status === "passed") {
            workspaceStatus.classList.add(
                "tests-passed"
            );
        }

        if (status === "failed") {
            workspaceStatus.classList.add(
                "tests-failed"
            );
        }

        if (workspaceStatusText) {
            workspaceStatusText.textContent =
                message;
        }
    }

    function getTestElement(testId) {
        return document.querySelector(
            `.test-case[data-test-id="${testId}"]`
        );
    }

    function setTestState(
        testId,
        state
    ) {
        const testElement =
            getTestElement(testId);

        if (!testElement) {
            return;
        }

        const icon =
            testElement.querySelector(
                ".test-status-icon"
            );

        testElement.classList.remove(
            "running",
            "passed",
            "failed"
        );

        if (state === "running") {
            testElement.classList.add("running");

            if (icon) {
                icon.textContent = "…";
            }
        } else if (state === "passed") {
            testElement.classList.add("passed");

            if (icon) {
                icon.textContent = "✓";
            }
        } else if (state === "failed") {
            testElement.classList.add("failed");

            if (icon) {
                icon.textContent = "×";
            }
        } else if (icon) {
            icon.textContent = "○";
        }
    }

    function resetTestDisplay() {
        requiredTestIds.forEach((testId) => {
            setTestState(testId, "pending");
        });

        passedTests = [];
        submitButton.disabled = true;
    }

    /*
        * This is a controlled simulator. It does not execute
        * arbitrary Python code on the Flask server.
        *
        * It checks whether the submitted solution contains the
        * important validation behavior required by the task.
        */
    function analyzeSubmittedCode(code) {
        const hasOrderCreation =
            /create_order_item\s*\(\s*product_id\s*\)/.test(
                code
            );

        const hasSuccessResponse =
            /return[\s\S]*,\s*201\b/.test(
                code
            );

        const usesSafeGet =
            /item\s*\.\s*get\s*\(\s*["']product_id["']\s*\)/.test(
                code
            );

        const checksMissingValue =
            /if\s+(?:not\s+product_id|product_id\s+is\s+None|product_id\s*==\s*None)\s*:/.test(
                code
            );

        const checksFieldBeforeAccess =
            /if\s+["']product_id["']\s+not\s+in\s+item\s*:/.test(
                code
            );

        const returnsClientError =
            /(?:,\s*400\b|["']status["']\s*:\s*400\b|status_code\s*=\s*400\b)/.test(
                code
            );

        const usesUnsafeDirectAccess =
            /item\s*\[\s*["']product_id["']\s*\]/.test(
                code
            );

        const validCartPasses =
            hasOrderCreation &&
            hasSuccessResponse;

        const missingProductIdPasses =
            returnsClientError &&
            (
                checksFieldBeforeAccess ||
                (
                    usesSafeGet &&
                    checksMissingValue
                )
            );

        const noServerCrashPasses =
            !usesUnsafeDirectAccess ||
            checksFieldBeforeAccess;

        return {
            valid_cart: validCartPasses,
            missing_product_id:
                missingProductIdPasses,
            no_server_crash:
                noServerCrashPasses
        };
    }

    function buildTerminalOutput(results) {
        const lines = [
            "$ pytest tests/test_checkout_service.py -q",
            ""
        ];

        const testDescriptions = {
            valid_cart:
                "test_valid_cart_creates_order",
            missing_product_id:
                "test_missing_product_id_returns_400",
            no_server_crash:
                "test_invalid_payload_does_not_crash"
        };

        requiredTestIds.forEach((testId) => {
            const passed = results[testId];

            lines.push(
                `${passed ? "PASSED" : "FAILED"}  ${testDescriptions[testId]}`
            );
        });

        const passedCount =
            requiredTestIds.filter(
                (testId) => results[testId]
            ).length;

        lines.push("");
        lines.push(
            `${passedCount} passed, ${
                requiredTestIds.length - passedCount
            } failed`
        );

        if (!results.valid_cart) {
            lines.push("");
            lines.push(
                "Check that valid cart items still call create_order_item(product_id) and return 201."
            );
        }

        if (!results.missing_product_id) {
            lines.push("");
            lines.push(
                "The missing product_id case must return a clear 400 client response."
            );
        }

        if (!results.no_server_crash) {
            lines.push("");
            lines.push(
                "Direct item['product_id'] access may still raise an unhandled KeyError."
            );
        }

        if (passedCount === requiredTestIds.length) {
            lines.push("");
            lines.push(
                "All checks passed. The fix is ready for submission."
            );
        }

        return lines.join("\n");
    }

    function runTests() {
        const submittedCode =
            codeEditor.value.trim();

        testRuns += 1;
        updateRunCounter();

        submitButton.disabled = true;
        runTestsButton.disabled = true;
        runTestsButton.textContent =
            "Running...";

        updateWorkspaceStatus(
            "pending",
            "Running tests"
        );

        requiredTestIds.forEach((testId) => {
            setTestState(testId, "running");
        });

        testOutput.textContent = [
            "$ pytest tests/test_checkout_service.py -q",
            "",
            "Collecting tests...",
            "Running checkout service checks..."
        ].join("\n");

        window.setTimeout(() => {
            const results =
                analyzeSubmittedCode(
                    submittedCode
                );

            passedTests =
                requiredTestIds.filter(
                    (testId) => results[testId]
                );

            requiredTestIds.forEach((testId) => {
                setTestState(
                    testId,
                    results[testId]
                        ? "passed"
                        : "failed"
                );
            });

            testOutput.textContent =
                buildTerminalOutput(results);

            lastTestedCode =
                codeEditor.value;

            const allTestsPassed =
                passedTests.length ===
                requiredTestIds.length;

            submitButton.disabled =
                !allTestsPassed;

            if (allTestsPassed) {
                if (guidedFixPanel) {
                    guidedFixPanel.hidden = true;
                }

                updateWorkspaceStatus(
                    "passed",
                    "All tests passed"
                );

                submitButton.textContent =
                    "Submit Working Fix";
            } else {
                failedTestRuns += 1;

                if (
                    guidedFixPanel &&
                    failedTestRuns >= 3
                ) {
                    guidedFixPanel.hidden = false;
                }

                updateWorkspaceStatus(
                    "failed",
                    "Tests need attention"
                );

                submitButton.textContent =
                    "Pass the Tests to Continue";
            }

            runTestsButton.disabled = false;
            runTestsButton.textContent =
                "▶ Run Tests";
        }, 700);
    }

    function invalidatePreviousResults() {
        if (
            lastTestedCode === null ||
            codeEditor.value === lastTestedCode
        ) {
            return;
        }

        resetTestDisplay();

        updateWorkspaceStatus(
            "pending",
            "Code changed — rerun tests"
        );

        submitButton.textContent =
            "Pass the Tests to Continue";
    }

    function restoreSavedResponse() {
        const savedValue =
            hiddenAnswer.dataset.savedAnswer;

        if (!savedValue) {
            updateLineNumbers();
            updateRunCounter();
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

            if (
                typeof savedResponse.submitted_code ===
                "string"
            ) {
                codeEditor.value =
                    savedResponse.submitted_code;
            }

            testRuns =
                Number(
                    savedResponse.test_runs
                ) || 0;

            hintsUsed =
                Number(
                    savedResponse.hints_used
                ) || 0;

            hintWasCounted =
                hintsUsed > 0;

            if (
                Array.isArray(
                    savedResponse.passed_tests
                )
            ) {
                passedTests =
                    savedResponse.passed_tests.filter(
                        (testId) =>
                            requiredTestIds.includes(
                                testId
                            )
                    );
            }

            const allTestsPassed =
                passedTests.length ===
                requiredTestIds.length;

            if (allTestsPassed) {
                requiredTestIds.forEach(
                    (testId) => {
                        setTestState(
                            testId,
                            "passed"
                        );
                    }
                );

                lastTestedCode =
                    codeEditor.value;

                submitButton.disabled = false;
                submitButton.textContent =
                    "Submit Working Fix";

                updateWorkspaceStatus(
                    "passed",
                    "All tests passed"
                );

                testOutput.textContent =
                    "Saved successful test results restored.";
            }

        } catch (error) {
            console.warn(
                "Could not restore the saved Code Lab response."
            );
        }

        updateLineNumbers();
        updateRunCounter();
    }

    /*
        * Allow Tab indentation inside the code editor.
        */
    codeEditor.addEventListener(
        "keydown",
        (event) => {
            if (event.key !== "Tab") {
                return;
            }

            event.preventDefault();

            const start =
                codeEditor.selectionStart;

            const end =
                codeEditor.selectionEnd;

            codeEditor.value =
                codeEditor.value.substring(
                    0,
                    start
                ) +
                "    " +
                codeEditor.value.substring(end);

            codeEditor.selectionStart =
                codeEditor.selectionEnd =
                    start + 4;

            updateLineNumbers();
            invalidatePreviousResults();
        }
    );

    codeEditor.addEventListener(
        "input",
        () => {
            updateLineNumbers();
            invalidatePreviousResults();
        }
    );

    codeEditor.addEventListener(
        "scroll",
        () => {
            if (lineNumbers) {
                lineNumbers.scrollTop =
                    codeEditor.scrollTop;
            }
        }
    );

    if (resetButton) {
        resetButton.addEventListener(
            "click",
            () => {
                codeEditor.value =
                    initialCode;

                lastTestedCode = null;

                resetTestDisplay();
                updateLineNumbers();

                testOutput.textContent =
                    "Code reset. Run the tests again.";

                updateWorkspaceStatus(
                    "pending",
                    "Tests not run"
                );

                submitButton.textContent =
                    "Pass the Tests to Continue";
            }
        );
    }

    if (hintButton && hintBox) {
        hintButton.addEventListener(
            "click",
            () => {
                const willShow =
                    hintBox.hidden;

                hintBox.hidden =
                    !willShow;

                hintButton.textContent =
                    willShow
                        ? "Hide hint"
                        : "Show hint";

                if (
                    willShow &&
                    !hintWasCounted
                ) {
                    hintsUsed += 1;
                    hintWasCounted = true;
                }
            }
        );
    }

    if (
    applyGuidedFixButton &&
    guidedFixPanel
) {
    applyGuidedFixButton.addEventListener(
        "click",
        () => {
            codeEditor.value =
                guidedSolution;

            guidedFixUsed = true;
            lastTestedCode = null;

            resetTestDisplay();
            updateLineNumbers();

            testOutput.textContent = [
                "Guided fix applied.",
                "",
                "Review the validation changes,",
                "then run the tests again."
            ].join("\n");

            updateWorkspaceStatus(
                "pending",
                "Guided fix applied — rerun tests"
            );

            submitButton.textContent =
                "Pass the Tests to Continue";

            guidedFixPanel.hidden = true;

            codeEditor.focus();
        }
    );
}

    runTestsButton.addEventListener(
        "click",
        runTests
    );

    form.addEventListener(
        "submit",
        (event) => {
            const code =
                codeEditor.value.trim();

            const allTestsPassed =
                passedTests.length ===
                requiredTestIds.length;

            const codeMatchesLastTest =
                codeEditor.value ===
                lastTestedCode;

            if (
                !allTestsPassed ||
                !codeMatchesLastTest
            ) {
                event.preventDefault();

                testOutput.textContent +=
                    "\n\nRun the tests successfully before submitting.";

                return;
            }

            const responseData = {
            task_type: "code_lab",
            issue_id: "API-184",
            submitted_code: code,
            test_runs: testRuns,
            failed_test_runs: failedTestRuns,
            passed_tests: passedTests,
            hints_used: hintsUsed,
            guided_fix_used: guidedFixUsed
        };

            hiddenAnswer.value =
                JSON.stringify(responseData);
        }
    );

    restoreSavedResponse();
}

if (
    document.readyState === "loading"
) {
    document.addEventListener(
        "DOMContentLoaded",
        initializeCodeLab
    );
} else {
    initializeCodeLab();
}
})();