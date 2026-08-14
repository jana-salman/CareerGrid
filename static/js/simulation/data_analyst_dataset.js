(() => {
    function initializeDataAnalystDataset() {
        const workspace =
            document.getElementById("daDatasetWorkspace");

        if (!workspace) {
            return;
        }

        const form =
            document.getElementById("dataAnalystDatasetForm");

        const hiddenAnswer =
            document.getElementById("dataAnalystDatasetAnswer");

        const inspectSummaryBtn =
            document.getElementById("inspectSummaryBtn");

        const checkDuplicatesBtn =
            document.getElementById("checkDuplicatesBtn");

        const checkMissingBtn =
            document.getElementById("checkMissingBtn");

        const analysisResult =
            document.getElementById("analysisResult");

        const rowCheckboxes =
            Array.from(
                document.querySelectorAll(
                    ".da-row-checkbox"
                )
            );

        const rootCauseSelect =
            document.getElementById("rootCauseSelect");

        const analystFinding =
            document.getElementById("analystFinding");

        const analystFindingCount =
            document.getElementById("analystFindingCount");

        const selectedRowCount =
            document.getElementById("selectedRowCount");

        const submitButton =
            document.getElementById("submitDatasetBtn");


        let inspectedSummary = false;
        let checkedDuplicates = false;
        let checkedMissingValues = false;


        function markButtonComplete(button) {
            button.classList.add("is-complete");
        }


        function inspectSummary() {
            inspectedSummary = true;

            markButtonComplete(inspectSummaryBtn);

            analysisResult.innerHTML =
                "<strong>Summary:</strong> " +
                "10 rows are loaded. The dashboard reports " +
                "$15,950 while Finance reports $14,750, " +
                "creating a $1,200 difference.";

            updateSubmissionState();
        }


        function checkDuplicates() {
            checkedDuplicates = true;

            markButtonComplete(checkDuplicatesBtn);

            document
                .querySelectorAll(
                    '[data-duplicate="true"]'
                )
                .forEach(
                    (row) => {
                        row.classList.add(
                            "is-duplicate"
                        );
                    }
                );

            analysisResult.innerHTML =
                "<strong>Duplicate check:</strong> " +
                "Rows 4 and 5 share the same Order ID, date, " +
                "product, quantity, unit price, and revenue.";

            updateSubmissionState();
        }


        function checkMissingValues() {
            checkedMissingValues = true;

            markButtonComplete(checkMissingBtn);

            document
                .querySelectorAll(
                    '[data-missing="true"]'
                )
                .forEach(
                    (row) => {
                        row.classList.add(
                            "is-missing"
                        );
                    }
                );

            analysisResult.innerHTML =
                "<strong>Missing-value check:</strong> " +
                "Row 6 has no region value. This is a quality issue, " +
                "but by itself it does not explain a $1,200 revenue difference.";

            updateSubmissionState();
        }


        function getSelectedRows() {
            return rowCheckboxes
                .filter(
                    (checkbox) => checkbox.checked
                )
                .map(
                    (checkbox) =>
                        Number(checkbox.value)
                );
        }


        function updateSelectedRows() {
            const selectedRows =
                getSelectedRows();

            selectedRowCount.textContent =
                `${selectedRows.length} row` +
                `${selectedRows.length === 1 ? "" : "s"} selected`;

            rowCheckboxes.forEach(
                (checkbox) => {
                    const row =
                        checkbox.closest("tr");

                    row.classList.toggle(
                        "is-selected",
                        checkbox.checked
                    );
                }
            );

            updateSubmissionState();
        }


        function updateCharacterCount() {
            analystFindingCount.textContent =
                `${analystFinding.value.length} / 1200`;

            updateSubmissionState();
        }


        function updateSubmissionState() {
            const selectedRows =
                getSelectedRows();

            const ready =
                inspectedSummary &&
                checkedDuplicates &&
                checkedMissingValues &&
                selectedRows.length >= 2 &&
                rootCauseSelect.value !== "" &&
                analystFinding.value.trim().length >= 40;

            submitButton.disabled = !ready;

            submitButton.textContent =
                ready
                    ? "Submit Investigation"
                    : "Complete Investigation";
        }


        function restoreSavedAnswer() {
            const savedValue =
                hiddenAnswer.dataset.savedAnswer;

            if (!savedValue) {
                updateCharacterCount();
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

                inspectedSummary =
                    Boolean(
                        savedResponse.inspected_summary
                    );

                checkedDuplicates =
                    Boolean(
                        savedResponse.checked_duplicates
                    );

                checkedMissingValues =
                    Boolean(
                        savedResponse.checked_missing_values
                    );

                if (inspectedSummary) {
                    markButtonComplete(
                        inspectSummaryBtn
                    );
                }

                if (checkedDuplicates) {
                    checkDuplicates();
                }

                if (checkedMissingValues) {
                    checkMissingValues();
                }

                const savedRows =
                    Array.isArray(
                        savedResponse.selected_rows
                    )
                        ? savedResponse.selected_rows
                        : [];

                rowCheckboxes.forEach(
                    (checkbox) => {
                        checkbox.checked =
                            savedRows.includes(
                                Number(
                                    checkbox.value
                                )
                            );
                    }
                );

                rootCauseSelect.value =
                    savedResponse.selected_root_cause || "";

                analystFinding.value =
                    savedResponse.analyst_finding || "";

            } catch (error) {
                console.warn(
                    "Could not restore the Data Analyst dataset response."
                );
            }

            updateSelectedRows();
            updateCharacterCount();
        }


        inspectSummaryBtn.addEventListener(
            "click",
            inspectSummary
        );

        checkDuplicatesBtn.addEventListener(
            "click",
            checkDuplicates
        );

        checkMissingBtn.addEventListener(
            "click",
            checkMissingValues
        );

        rowCheckboxes.forEach(
            (checkbox) => {
                checkbox.addEventListener(
                    "change",
                    updateSelectedRows
                );
            }
        );

        rootCauseSelect.addEventListener(
            "change",
            updateSubmissionState
        );

        analystFinding.addEventListener(
            "input",
            updateCharacterCount
        );


        form.addEventListener(
            "submit",
            (event) => {
                const selectedRows =
                    getSelectedRows();

                if (
                    !inspectedSummary ||
                    !checkedDuplicates ||
                    !checkedMissingValues ||
                    selectedRows.length < 2 ||
                    !rootCauseSelect.value ||
                    analystFinding.value.trim().length < 40
                ) {
                    event.preventDefault();
                    updateSubmissionState();
                    return;
                }

                const responseData = {
                    task_type:
                        "data_analyst_dataset",

                    issue_id:
                        "DA-2104",

                    inspected_summary:
                        inspectedSummary,

                    checked_duplicates:
                        checkedDuplicates,

                    checked_missing_values:
                        checkedMissingValues,

                    selected_rows:
                        selectedRows,

                    selected_root_cause:
                        rootCauseSelect.value,

                    analyst_finding:
                        analystFinding.value.trim()
                };

                hiddenAnswer.value =
                    JSON.stringify(
                        responseData
                    );
            }
        );


        restoreSavedAnswer();
    }


    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializeDataAnalystDataset
        );
    } else {
        initializeDataAnalystDataset();
    }
})();