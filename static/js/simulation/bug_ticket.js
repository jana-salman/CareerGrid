(() => {
    "use strict";

    function initializeApiTestingWorkspace() {
        const form =
            document.getElementById(
                "api-testing-form"
            );

        // Other simulation steps do not contain this form.
        if (!form) {
            return;
        }

        const hiddenAnswer =
            document.getElementById("answer");

        const testButtons = Array.from(
            document.querySelectorAll(
                ".api-test-case"
            )
        );

        const requestPayload =
            document.getElementById(
                "request-payload"
            );

        const sendRequestButton =
            document.getElementById(
                "send-request-button"
            );

        const responseStatus =
            document.getElementById(
                "response-status"
            );

        const responseBody =
            document.getElementById(
                "response-body"
            );

        const submitButton =
            document.getElementById(
                "submit-api-testing-button"
            );

        const testingStatus =
            document.querySelector(
                ".api-testing-status"
            );

        const testingStatusText =
            document.getElementById(
                "api-testing-status-text"
            );

        const requiredElements = [
            hiddenAnswer,
            requestPayload,
            sendRequestButton,
            responseStatus,
            responseBody,
            submitButton
        ];

        if (
            requiredElements.some(
                (element) => !element
            )
        ) {
            console.error(
                "CareerGrid API testing workspace could not start."
            );

            return;
        }

        const testCases = {
            "valid-cart": {
                testId: "valid_cart",

                payload: {
                    cart_items: [
                        {
                            product_id: "P-104",
                            quantity: 2
                        },
                        {
                            product_id: "P-205",
                            quantity: 1
                        }
                    ]
                },

                expectedStatus: 201,
                actualStatus: 201,
                statusLabel: "201 Created",

                response: {
                    status: "created",
                    order_id: "ORD-9021",
                    items_created: 2
                }
            },

            "missing-product-id": {
                testId: "missing_product_id",

                payload: {
                    cart_items: [
                        {
                            quantity: 2
                        }
                    ]
                },

                expectedStatus: 400,
                actualStatus: 400,
                statusLabel: "400 Bad Request",

                response: {
                    error: "product_id is required",
                    field: "product_id"
                }
            },

            "null-product-id": {
                testId: "null_product_id",

                payload: {
                    cart_items: [
                        {
                            product_id: null,
                            quantity: 1
                        }
                    ]
                },

                expectedStatus: 400,
                actualStatus: 400,
                statusLabel: "400 Bad Request",

                response: {
                    error: "product_id is required",
                    field: "product_id"
                }
            }
        };

        const completedTests = new Map();

        let selectedTestId = null;
        let requestCount = 0;
        let requestIsRunning = false;

        function allTestsAreComplete() {
            return Object.keys(
                testCases
            ).every(
                (testId) =>
                    completedTests.has(testId)
            );
        }

        function updateHiddenAnswer() {
            const orderedResults = Object.keys(
                testCases
            )
                .filter(
                    (testId) =>
                        completedTests.has(testId)
                )
                .map(
                    (testId) =>
                        completedTests.get(testId)
                );

            const allTestsPassed =
                orderedResults.length ===
                    Object.keys(testCases).length &&
                orderedResults.every(
                    (result) => result.passed
                );

            const answer = {
                task_type: "api_testing",

                endpoint: {
                    method: "POST",
                    path: "/api/checkout"
                },

                tests_run: orderedResults,

                request_count: requestCount,

                all_tests_passed: allTestsPassed,

                release_decision: allTestsPassed
                    ? "ready_for_review"
                    : "testing_in_progress"
            };

            hiddenAnswer.value =
                JSON.stringify(answer);
        }

        function updateProgressStatus() {
            const completedCount =
                completedTests.size;

            const totalCount =
                Object.keys(testCases).length;

            if (allTestsAreComplete()) {
                if (testingStatusText) {
                    testingStatusText.textContent =
                        "All required tests passed";
                }

                if (testingStatus) {
                    testingStatus.classList.add(
                        "tests-complete"
                    );
                }

                submitButton.disabled = false;
            } else {
                if (testingStatusText) {
                    testingStatusText.textContent =
                        `${completedCount} of ${totalCount} tests completed`;
                }

                if (testingStatus) {
                    testingStatus.classList.remove(
                        "tests-complete"
                    );
                }

                submitButton.disabled = true;
            }

            updateHiddenAnswer();
        }

        function markTestAsPassed(testId) {
            const testButton =
                testButtons.find(
                    (button) =>
                        button.dataset.testId ===
                        testId
                );

            if (!testButton) {
                return;
            }

            testButton.classList.remove(
                "is-failed"
            );

            testButton.classList.add(
                "is-passed"
            );

            const resultIcon =
                testButton.querySelector(
                    ".test-result-icon"
                );

            if (resultIcon) {
                resultIcon.textContent = "✓";
            }
        }

        function selectTest(testId) {
            if (
                requestIsRunning ||
                !testCases[testId]
            ) {
                return;
            }

            selectedTestId = testId;

            testButtons.forEach((button) => {
                button.classList.toggle(
                    "active",
                    button.dataset.testId ===
                        testId
                );
            });

            const selectedTest =
                testCases[testId];

            requestPayload.value =
                JSON.stringify(
                    selectedTest.payload,
                    null,
                    4
                );

            responseStatus.className =
                "response-status";

            responseStatus.textContent =
                "Ready to send";

            responseBody.textContent =
                JSON.stringify(
                    {
                        message:
                            "Click Send Request to execute this test."
                    },
                    null,
                    4
                );

            sendRequestButton.disabled = false;
            sendRequestButton.textContent =
                completedTests.has(testId)
                    ? "Run Test Again"
                    : "Send Request";
        }

        function runSelectedTest() {
            if (
                !selectedTestId ||
                requestIsRunning
            ) {
                return;
            }

            const runningTestId =
                selectedTestId;

            const selectedTest =
                testCases[runningTestId];

            requestIsRunning = true;

            sendRequestButton.disabled = true;
            sendRequestButton.textContent =
                "Sending Request...";

            responseStatus.className =
                "response-status";

            responseStatus.textContent =
                "Request running";

            responseBody.textContent =
                JSON.stringify(
                    {
                        message:
                            "Contacting the checkout service..."
                    },
                    null,
                    4
                );

            window.setTimeout(() => {
                requestCount += 1;

                const passed =
                    selectedTest.actualStatus ===
                    selectedTest.expectedStatus;

                const testResult = {
                    test_id:
                        selectedTest.testId,

                    expected_status:
                        selectedTest.expectedStatus,

                    actual_status:
                        selectedTest.actualStatus,

                    passed: passed
                };

                completedTests.set(
                    runningTestId,
                    testResult
                );

                if (passed) {
                    markTestAsPassed(
                        runningTestId
                    );
                }

                responseStatus.className =
                    selectedTest.actualStatus < 300
                        ? "response-status success"
                        : "response-status warning";

                responseStatus.textContent =
                    selectedTest.statusLabel;

                responseBody.textContent =
                    JSON.stringify(
                        selectedTest.response,
                        null,
                        4
                    );

                requestIsRunning = false;

                sendRequestButton.disabled = false;
                sendRequestButton.textContent =
                    "Run Test Again";

                updateProgressStatus();
            }, 650);
        }

        function restoreSavedProgress() {
            const savedAnswer =
                hiddenAnswer.dataset.savedAnswer;

            if (!savedAnswer) {
                updateProgressStatus();
                return;
            }

            try {
                const parsedAnswer =
                    JSON.parse(savedAnswer);

                requestCount =
                    Number(
                        parsedAnswer.request_count
                    ) || 0;

                const savedTests =
                    Array.isArray(
                        parsedAnswer.tests_run
                    )
                        ? parsedAnswer.tests_run
                        : [];

                savedTests.forEach(
                    (savedTest) => {
                        const matchingTestId =
                            Object.keys(
                                testCases
                            ).find(
                                (testId) =>
                                    testCases[testId]
                                        .testId ===
                                    savedTest.test_id
                            );

                        if (!matchingTestId) {
                            return;
                        }

                        completedTests.set(
                            matchingTestId,
                            savedTest
                        );

                        if (savedTest.passed) {
                            markTestAsPassed(
                                matchingTestId
                            );
                        }
                    }
                );
            } catch (error) {
                console.warn(
                    "The saved API testing response could not be restored.",
                    error
                );
            }

            updateProgressStatus();
        }

        testButtons.forEach((button) => {
            button.addEventListener(
                "click",
                () => {
                    selectTest(
                        button.dataset.testId
                    );
                }
            );
        });

        sendRequestButton.addEventListener(
            "click",
            runSelectedTest
        );

        form.addEventListener(
            "submit",
            (event) => {
                if (!allTestsAreComplete()) {
                    event.preventDefault();

                    responseStatus.className =
                        "response-status error";

                    responseStatus.textContent =
                        "Testing incomplete";

                    responseBody.textContent =
                        JSON.stringify(
                            {
                                error:
                                    "Run all required test cases before continuing."
                            },
                            null,
                            4
                        );

                    return;
                }

                updateHiddenAnswer();
            }
        );

        restoreSavedProgress();
    }

    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializeApiTestingWorkspace
        );
    } else {
        initializeApiTestingWorkspace();
    }
})();