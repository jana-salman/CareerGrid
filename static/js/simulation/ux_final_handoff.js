function initUXFinalHandoff() {

    const form =
        document.getElementById("ux-handoff-form");

    const answerInput =
        document.getElementById("ux-handoff-answer");

    if (!form || !answerInput) {
        return;
    }


    const evidenceCheckboxes =
        document.querySelectorAll(
            ".ux-handoff-evidence"
        );

    const kpiCheckboxes =
        document.querySelectorAll(
            ".ux-kpi"
        );

    const recommendationRadios =
        document.querySelectorAll(
            'input[name="ux_final_recommendation"]'
        );

    const evidenceCount =
        document.getElementById(
            "ux-evidence-count"
        );

    const kpiCount =
        document.getElementById(
            "ux-kpi-count"
        );

    const messageInput =
        document.getElementById(
            "ux-stakeholder-message"
        );

    const messageLength =
        document.getElementById(
            "ux-message-length"
        );

    const priorityContainer =
        document.getElementById(
            "ux-action-priority"
        );

    const previewButton =
        document.getElementById(
            "ux-preview-handoff"
        );

    const previewPanel =
        document.getElementById(
            "ux-handoff-preview"
        );

    const previewRecommendation =
        document.getElementById(
            "ux-preview-recommendation"
        );

    const previewEvidence =
        document.getElementById(
            "ux-preview-evidence"
        );

    const previewKpis =
        document.getElementById(
            "ux-preview-kpis"
        );

    const previewMessage =
        document.getElementById(
            "ux-preview-message"
        );

    const statusBox =
        document.getElementById(
            "ux-handoff-status"
        );

    const submitButton =
        document.getElementById(
            "ux-handoff-submit"
        );


    let handoffGenerated = false;


    const LABELS = {

        funnel_drop:
            "Checkout funnel abandonment",

        interview:
            "User interview evidence",

        usability:
            "Usability-session behavior",

        support:
            "Customer-support patterns",

        visual_preference:
            "Visual preference",

        stakeholder_opinion:
            "Stakeholder preference",


        checkout_completion:
            "Checkout completion rate",

        checkout_time:
            "Time to complete checkout",

        account_creation_rate:
            "Optional account creation",

        error_rate:
            "Checkout error rate",

        page_views:
            "Homepage page views",

        social_followers:
            "Social follower growth",


        keep_current:
            "Keep current checkout",

        guest_checkout:
            "Launch guest checkout",

        full_redesign:
            "Delay for full redesign"
    };


    function setStatus(message, type = "") {

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


    function getCheckedValues(elements) {

        return Array.from(elements)
            .filter(
                element => element.checked
            )
            .map(
                element => element.value
            );
    }


    function getRecommendation() {

        const selected =
            document.querySelector(
                'input[name="ux_final_recommendation"]:checked'
            );

        return selected
            ? selected.value
            : "";
    }


    function getActionPriority() {

        return Array.from(
            priorityContainer.querySelectorAll(
                ".ux-priority-item"
            )
        ).map(
            item => item.dataset.action
        );
    }


    function updateAnswer() {

        answerInput.value =
            JSON.stringify({

                task_type:
                    "ux_final_handoff",

                issue_id:
                    "UX-2048",

                selected_evidence:
                    getCheckedValues(
                        evidenceCheckboxes
                    ),

                recommendation:
                    getRecommendation(),

                success_metrics:
                    getCheckedValues(
                        kpiCheckboxes
                    ),

                action_priority:
                    getActionPriority(),

                stakeholder_message:
                    messageInput.value.trim(),

                handoff_generated:
                    handoffGenerated
            });
    }


    function enforceLimit(
        checkbox,
        allCheckboxes,
        limit
    ) {

        const selected =
            getCheckedValues(
                allCheckboxes
            );

        if (selected.length > limit) {

            checkbox.checked = false;

            setStatus(
                `You may select only ${limit}. Prioritize the strongest choices.`,
                "warning"
            );

            return false;
        }

        return true;
    }


    evidenceCheckboxes.forEach(
        checkbox => {

            checkbox.addEventListener(
                "change",
                () => {

                    enforceLimit(
                        checkbox,
                        evidenceCheckboxes,
                        3
                    );

                    const count =
                        getCheckedValues(
                            evidenceCheckboxes
                        ).length;

                    evidenceCount.textContent =
                        `${count} / 3 selected`;

                    handoffGenerated = false;

                    updateAnswer();
                }
            );
        }
    );


    kpiCheckboxes.forEach(
        checkbox => {

            checkbox.addEventListener(
                "change",
                () => {

                    enforceLimit(
                        checkbox,
                        kpiCheckboxes,
                        3
                    );

                    const count =
                        getCheckedValues(
                            kpiCheckboxes
                        ).length;

                    kpiCount.textContent =
                        `${count} / 3 selected`;

                    handoffGenerated = false;

                    updateAnswer();
                }
            );
        }
    );


    recommendationRadios.forEach(
        radio => {

            radio.addEventListener(
                "change",
                () => {

                    handoffGenerated = false;

                    updateAnswer();
                }
            );
        }
    );


    messageInput.addEventListener(
        "input",
        () => {

            const length =
                messageInput.value.length;

            messageLength.textContent =
                `${length} characters`;

            handoffGenerated = false;

            updateAnswer();
        }
    );


    priorityContainer.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }


            const item =
                button.closest(
                    ".ux-priority-item"
                );

            if (!item) {
                return;
            }


            if (
                button.classList.contains(
                    "ux-move-up"
                )
            ) {

                const previous =
                    item.previousElementSibling;

                if (previous) {

                    priorityContainer.insertBefore(
                        item,
                        previous
                    );
                }
            }


            if (
                button.classList.contains(
                    "ux-move-down"
                )
            ) {

                const next =
                    item.nextElementSibling;

                if (next) {

                    priorityContainer.insertBefore(
                        next,
                        item
                    );
                }
            }


            handoffGenerated = false;

            updateAnswer();
        }
    );


    function renderList(
        container,
        values
    ) {

        container.innerHTML = "";

        values.forEach(
            value => {

                const li =
                    document.createElement(
                        "li"
                    );

                li.textContent =
                    LABELS[value] || value;

                container.appendChild(li);
            }
        );
    }


    previewButton.addEventListener(
        "click",
        () => {

            const evidence =
                getCheckedValues(
                    evidenceCheckboxes
                );

            const kpis =
                getCheckedValues(
                    kpiCheckboxes
                );

            const recommendation =
                getRecommendation();

            const message =
                messageInput.value.trim();


            if (evidence.length !== 3) {

                setStatus(
                    "Select exactly 3 pieces of evidence.",
                    "warning"
                );

                return;
            }


            if (!recommendation) {

                setStatus(
                    "Choose your final product recommendation.",
                    "warning"
                );

                return;
            }


            if (kpis.length !== 3) {

                setStatus(
                    "Choose exactly 3 success metrics.",
                    "warning"
                );

                return;
            }


            if (message.length < 120) {

                setStatus(
                    "Your stakeholder message needs more detail before handoff.",
                    "warning"
                );

                messageInput.focus();

                return;
            }


            previewRecommendation.textContent =
                LABELS[recommendation];

            renderList(
                previewEvidence,
                evidence
            );

            renderList(
                previewKpis,
                kpis
            );

            previewMessage.textContent =
                message;


            previewPanel.hidden = false;

            handoffGenerated = true;


            if (
                recommendation ===
                "guest_checkout"
                &&
                evidence.includes(
                    "funnel_drop"
                )
                &&
                (
                    evidence.includes(
                        "interview"
                    )
                    ||
                    evidence.includes(
                        "usability"
                    )
                )
                &&
                kpis.includes(
                    "checkout_completion"
                )
            ) {

                setStatus(
                    "Strong handoff. Your recommendation is supported by behavioral evidence and measurable success criteria.",
                    "success"
                );
            }

            else {

                setStatus(
                    "Handoff generated. Consider whether your strongest evidence and KPIs directly support the product decision.",
                    "warning"
                );
            }


            updateAnswer();


            previewPanel.scrollIntoView({
                behavior: "smooth",
                block: "nearest"
            });
        }
    );


    form.addEventListener(
        "submit",
        event => {

            const evidence =
                getCheckedValues(
                    evidenceCheckboxes
                );

            const kpis =
                getCheckedValues(
                    kpiCheckboxes
                );

            const recommendation =
                getRecommendation();

            const message =
                messageInput.value.trim();


            if (evidence.length !== 3) {

                event.preventDefault();

                setStatus(
                    "Select exactly 3 pieces of supporting evidence.",
                    "error"
                );

                return;
            }


            if (!recommendation) {

                event.preventDefault();

                setStatus(
                    "Choose your final recommendation.",
                    "error"
                );

                return;
            }


            if (kpis.length !== 3) {

                event.preventDefault();

                setStatus(
                    "Select exactly 3 success metrics.",
                    "error"
                );

                return;
            }


            if (message.length < 120) {

                event.preventDefault();

                setStatus(
                    "Write a complete stakeholder recommendation.",
                    "error"
                );

                messageInput.focus();

                return;
            }


            if (!handoffGenerated) {

                event.preventDefault();

                setStatus(
                    "Generate and review your stakeholder handoff before finishing.",
                    "error"
                );

                return;
            }


            updateAnswer();


            submitButton.disabled = true;

            submitButton.textContent =
                "Finishing simulation...";
        }
    );


    updateAnswer();
}


if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initUXFinalHandoff
    );

} else {

    initUXFinalHandoff();
}