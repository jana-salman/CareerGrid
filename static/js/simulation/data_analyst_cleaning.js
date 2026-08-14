(() => {

    function initializeDataAnalystCleaning() {

        const workspace =
            document.getElementById(
                "daCleaningWorkspace"
            );

        if (!workspace) {
            return;
        }


        const form =
            document.getElementById(
                "dataAnalystCleaningForm"
            );

        const hiddenAnswer =
            document.getElementById(
                "dataAnalystCleaningAnswer"
            );

        const inspectReferenceBtn =
            document.getElementById(
                "inspectReferenceBtn"
            );

        const referenceResult =
            document.getElementById(
                "referenceResult"
            );

        const applyPreviewBtn =
            document.getElementById(
                "applyCleaningPreviewBtn"
            );

        const previewResult =
            document.getElementById(
                "cleaningPreviewResult"
            );

        const cleaningNote =
            document.getElementById(
                "cleaningNote"
            );

        const cleaningNoteCount =
            document.getElementById(
                "cleaningNoteCount"
            );

        const submitButton =
            document.getElementById(
                "submitCleaningBtn"
            );


        const duplicateRadios =
            Array.from(
                document.querySelectorAll(
                    'input[name="duplicateAction"]'
                )
            );

        const missingRegionRadios =
            Array.from(
                document.querySelectorAll(
                    'input[name="missingRegionAction"]'
                )
            );


        let inspectedReference = false;
        let previewApplied = false;
        let previewRowCount = 10;
        let previewRevenue = 15950;


        function selectedRadio(radios) {

            const selected =
                radios.find(
                    (radio) => radio.checked
                );

            return selected
                ? selected.value
                : "";
        }


        function getDuplicateAction() {
            return selectedRadio(
                duplicateRadios
            );
        }


        function getMissingRegionAction() {
            return selectedRadio(
                missingRegionRadios
            );
        }


        function updateChoiceStyles() {

            document
                .querySelectorAll(
                    ".da-cleaning-choice"
                )
                .forEach(
                    (choice) => {

                        const radio =
                            choice.querySelector(
                                'input[type="radio"]'
                            );

                        choice.classList.toggle(
                            "is-selected",
                            Boolean(
                                radio &&
                                radio.checked
                            )
                        );

                    }
                );

        }


        function resetPreview() {

            previewApplied = false;

            previewRowCount = 10;
            previewRevenue = 15950;

            previewResult.innerHTML =
                '<div class="da-preview-empty">' +
                "Your cleaning choices changed. " +
                "Apply the preview again to validate them." +
                "</div>";

        }


        function updatePreviewAvailability() {

            const ready =
                inspectedReference &&
                getDuplicateAction() !== "" &&
                getMissingRegionAction() !== "";

            applyPreviewBtn.disabled =
                !ready;

        }


        function inspectReference() {

            inspectedReference = true;

            referenceResult.hidden = false;

            inspectReferenceBtn.classList.add(
                "is-complete"
            );

            inspectReferenceBtn.textContent =
                "Reference Inspected ✓";

            updatePreviewAvailability();
            updateSubmissionState();

        }


        function calculatePreview() {

            let rowCount = 10;
            let revenue = 15950;


            const duplicateAction =
                getDuplicateAction();

            const missingAction =
                getMissingRegionAction();


            if (
                duplicateAction ===
                "remove_duplicate"
            ) {
                rowCount -= 1;
                revenue -= 1200;
            }


            if (
                duplicateAction ===
                "aggregate_records"
            ) {
                rowCount -= 1;
            }


            if (
                missingAction ===
                "drop_record"
            ) {
                rowCount -= 1;
                revenue -= 1800;
            }


            previewRowCount = rowCount;
            previewRevenue = revenue;

        }


        function formatCurrency(value) {

            return new Intl.NumberFormat(
                "en-US",
                {
                    style: "currency",
                    currency: "USD",
                    maximumFractionDigits: 0
                }
            ).format(value);

        }


        function applyPreview() {

            if (
                applyPreviewBtn.disabled
            ) {
                return;
            }


            calculatePreview();

            previewApplied = true;


            const difference =
                previewRevenue - 14750;


            let comparisonText;

            if (difference === 0) {

                comparisonText =
                    "Matches Finance";

            } else {

                comparisonText =
                    `${formatCurrency(
                        Math.abs(difference)
                    )} ${
                        difference > 0
                            ? "above"
                            : "below"
                    } Finance`;

            }


            previewResult.innerHTML = `
                <div class="da-preview-success">

                    <div class="da-preview-metric">
                        <span>Preview Rows</span>
                        <strong>
                            ${previewRowCount}
                        </strong>
                    </div>

                    <div class="da-preview-metric">
                        <span>Preview Revenue</span>
                        <strong>
                            ${formatCurrency(
                                previewRevenue
                            )}
                        </strong>
                    </div>

                    <div class="da-preview-metric">
                        <span>Finance Comparison</span>
                        <strong>
                            ${comparisonText}
                        </strong>
                    </div>

                </div>
            `;


            updateSubmissionState();

        }


        function updateCharacterCount() {

            cleaningNoteCount.textContent =
                `${cleaningNote.value.length} / 1200`;

            updateSubmissionState();

        }


        function updateSubmissionState() {

            const ready =
                inspectedReference &&
                previewApplied &&
                getDuplicateAction() !== "" &&
                getMissingRegionAction() !== "" &&
                cleaningNote.value.trim().length >= 40;

            submitButton.disabled =
                !ready;

            submitButton.textContent =
                ready
                    ? "Submit Cleaning"
                    : "Complete Cleaning";

        }


        function handleChoiceChange() {

            updateChoiceStyles();

            resetPreview();

            updatePreviewAvailability();

            updateSubmissionState();

        }


        function restoreSavedAnswer() {

            const savedValue =
                hiddenAnswer.dataset.savedAnswer;

            if (!savedValue) {

                updateChoiceStyles();
                updateCharacterCount();
                updatePreviewAvailability();

                return;

            }


            try {

                const saved =
                    JSON.parse(savedValue);


                if (
                    !saved ||
                    typeof saved !== "object"
                ) {
                    return;
                }


                duplicateRadios.forEach(
                    (radio) => {

                        radio.checked =
                            radio.value ===
                            saved.duplicate_action;

                    }
                );


                missingRegionRadios.forEach(
                    (radio) => {

                        radio.checked =
                            radio.value ===
                            saved.missing_region_action;

                    }
                );


                inspectedReference =
                    Boolean(
                        saved.inspected_reference
                    );


                if (inspectedReference) {

                    referenceResult.hidden =
                        false;

                    inspectReferenceBtn
                        .classList.add(
                            "is-complete"
                        );

                    inspectReferenceBtn
                        .textContent =
                            "Reference Inspected ✓";

                }


                cleaningNote.value =
                    saved.cleaning_note || "";


                if (
                    saved.preview_applied
                ) {

                    applyPreview();

                }


            } catch (error) {

                console.warn(
                    "Could not restore Data Analyst cleaning response."
                );

            }


            updateChoiceStyles();
            updateCharacterCount();
            updatePreviewAvailability();
            updateSubmissionState();

        }


        inspectReferenceBtn.addEventListener(
            "click",
            inspectReference
        );


        duplicateRadios.forEach(
            (radio) => {

                radio.addEventListener(
                    "change",
                    handleChoiceChange
                );

            }
        );


        missingRegionRadios.forEach(
            (radio) => {

                radio.addEventListener(
                    "change",
                    handleChoiceChange
                );

            }
        );


        applyPreviewBtn.addEventListener(
            "click",
            applyPreview
        );


        cleaningNote.addEventListener(
            "input",
            updateCharacterCount
        );


        form.addEventListener(
            "submit",
            (event) => {

                if (
                    !inspectedReference ||
                    !previewApplied ||
                    !getDuplicateAction() ||
                    !getMissingRegionAction() ||
                    cleaningNote.value.trim().length < 40
                ) {

                    event.preventDefault();

                    updateSubmissionState();

                    return;

                }


                const response = {

                    task_type:
                        "data_analyst_cleaning",

                    issue_id:
                        "DA-2104",

                    duplicate_action:
                        getDuplicateAction(),

                    missing_region_action:
                        getMissingRegionAction(),

                    inspected_reference:
                        inspectedReference,

                    preview_applied:
                        previewApplied,

                    preview_row_count:
                        previewRowCount,

                    preview_revenue:
                        previewRevenue,

                    cleaning_note:
                        cleaningNote.value.trim()

                };


                hiddenAnswer.value =
                    JSON.stringify(response);

            }
        );


        restoreSavedAnswer();

    }


    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initializeDataAnalystCleaning
        );

    } else {

        initializeDataAnalystCleaning();

    }

})();