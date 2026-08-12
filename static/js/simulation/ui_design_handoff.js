function initUIDesignHandoff() {
    const form = document.getElementById("ui-handoff-form");
    const answerInput = document.getElementById("ui-handoff-answer");

    if (!form || !answerInput) return;

    const visual = document.getElementById("ui-handoff-visual");
    const components = document.getElementById("ui-handoff-components");
    const responsive = document.getElementById("ui-handoff-responsive");
    const accessibility = document.getElementById("ui-handoff-accessibility");
    const message = document.getElementById("ui-handoff-message");

    const counter = document.getElementById("ui-handoff-count");
    const status = document.getElementById("ui-handoff-status");

    const priorityButtons =
        document.querySelectorAll(".ui-handoff-priority");

    let priority = "";


    function updateAnswer() {
        answerInput.value = JSON.stringify({
            task_type: "ui_design_handoff",
            issue_id: "UI-5102",

            visual_direction:
                visual ? visual.value.trim() : "",

            component_standards:
                components ? components.value.trim() : "",

            responsive_behavior:
                responsive ? responsive.value.trim() : "",

            accessibility_requirements:
                accessibility ? accessibility.value.trim() : "",

            implementation_priority:
                priority,

            final_message:
                message ? message.value.trim() : ""
        });
    }


    priorityButtons.forEach(button => {
        button.addEventListener("click", () => {

            priorityButtons.forEach(item =>
                item.classList.remove("active")
            );

            button.classList.add("active");

            priority =
                button.dataset.priority || "";

            updateAnswer();
        });
    });


    [
        visual,
        components,
        responsive,
        accessibility,
        message
    ].forEach(field => {

        if (!field) return;

        field.addEventListener("input", () => {

            if (field === message && counter) {
                counter.textContent =
                    `${message.value.length} characters`;
            }

            updateAnswer();
        });
    });


    form.addEventListener("submit", event => {

        const requiredFields = [
            visual,
            components,
            responsive,
            accessibility
        ];

        for (const field of requiredFields) {

            if (!field || field.value.trim().length < 30) {

                event.preventDefault();

                status.textContent =
                    "Complete every handoff section with meaningful implementation guidance.";

                status.classList.add(
                    "ui-handoff-status--error"
                );

                if (field) field.focus();

                return;
            }
        }


        if (!priority) {

            event.preventDefault();

            status.textContent =
                "Select an implementation priority.";

            status.classList.add(
                "ui-handoff-status--error"
            );

            return;
        }


        if (!message || message.value.trim().length < 80) {

            event.preventDefault();

            status.textContent =
                "Write a final engineering message of at least 80 characters.";

            status.classList.add(
                "ui-handoff-status--error"
            );

            if (message) message.focus();

            return;
        }


        status.classList.remove(
            "ui-handoff-status--error"
        );

        updateAnswer();
    });


    updateAnswer();
}


if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initUIDesignHandoff
    );
} else {
    initUIDesignHandoff();
}