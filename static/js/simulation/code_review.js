(() => {
    "use strict";

    function initializeCodeReviewTask() {
        const form = document.getElementById(
            "code-review-task-form"
        );

        if (!form) {
            return;
        }

        const hiddenAnswer =
            document.getElementById("answer");

        const reviewComment =
            document.getElementById("review-comment");

        const characterCount =
            document.getElementById(
                "review-comment-character-count"
            );

        if (!hiddenAnswer || !reviewComment) {
            console.error(
                "CareerGrid code review task could not start."
            );

            return;
        }

        function updateCharacterCount() {
            const currentLength =
                reviewComment.value.length;

            if (characterCount) {
                characterCount.textContent =
                    `${currentLength} / 1500`;
            }
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

                const selectedLine =
                    savedResponse.selected_line;

                const selectedFix =
                    savedResponse.selected_fix;

                if (selectedLine) {
                    const lineOption =
                        form.querySelector(
                            `input[name="selected_line"][value="${selectedLine}"]`
                        );

                    if (lineOption) {
                        lineOption.checked = true;
                    }
                }

                if (selectedFix) {
                    const fixOption =
                        form.querySelector(
                            `input[name="selected_fix"][value="${selectedFix}"]`
                        );

                    if (fixOption) {
                        fixOption.checked = true;
                    }
                }

                reviewComment.value =
                    savedResponse.review_comment || "";

            } catch (error) {
                /*
                 * Ignore older answers that were saved before
                 * Step 3 became interactive.
                 */
            }

            updateCharacterCount();
        }

        reviewComment.addEventListener(
            "input",
            () => {
                reviewComment.setCustomValidity("");
                updateCharacterCount();
            }
        );

        form.addEventListener(
            "submit",
            (event) => {
                const selectedLine =
                    form.querySelector(
                        'input[name="selected_line"]:checked'
                    );

                const selectedFix =
                    form.querySelector(
                        'input[name="selected_fix"]:checked'
                    );

                const comment =
                    reviewComment.value.trim();

                if (!selectedLine) {
                    event.preventDefault();

                    const firstLine =
                        form.querySelector(
                            'input[name="selected_line"]'
                        );

                    if (firstLine) {
                        firstLine.focus();
                        firstLine.reportValidity();
                    }

                    return;
                }

                if (!selectedFix) {
                    event.preventDefault();

                    const firstFix =
                        form.querySelector(
                            'input[name="selected_fix"]'
                        );

                    if (firstFix) {
                        firstFix.focus();
                        firstFix.reportValidity();
                    }

                    return;
                }

                if (comment.length < 20) {
                    event.preventDefault();

                    reviewComment.setCustomValidity(
                        "Please write a review comment of at least 20 characters."
                    );

                    reviewComment.reportValidity();
                    reviewComment.focus();

                    return;
                }

                if (comment.length > 1500) {
                    event.preventDefault();

                    reviewComment.setCustomValidity(
                        "Your review comment must contain no more than 1500 characters."
                    );

                    reviewComment.reportValidity();
                    reviewComment.focus();

                    return;
                }

                reviewComment.setCustomValidity("");

                const responseData = {
                    task_type: "code_review",
                    pull_request_id: "PR-184",
                    selected_line: selectedLine.value,
                    selected_fix: selectedFix.value,
                    review_comment: comment
                };

                hiddenAnswer.value =
                    JSON.stringify(responseData);
            }
        );

        restoreSavedAnswer();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeCodeReviewTask
        );
    } else {
        initializeCodeReviewTask();
    }
})();