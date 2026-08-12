function initUIComponentSystem() {
    const form = document.getElementById("ui-component-form");
    const answerInput = document.getElementById("ui-component-answer");

    if (!form || !answerInput) return;

    const preview = document.getElementById("ui-component-preview");
    const status = document.getElementById("ui-component-status");
    const rationale = document.getElementById("ui-component-rationale");
    const charCount = document.getElementById("ui-component-count");

    const selections = {
        primary_button: "solid",
        secondary_button: "outline",
        input_style: "outlined",
        focus_state: "ring",
        status_badge: "label_icon"
    };

    function updateAnswer() {
        answerInput.value = JSON.stringify({
            task_type: "ui_component_system",
            issue_id: "UI-3204",

            primary_button: selections.primary_button,
            secondary_button: selections.secondary_button,
            input_style: selections.input_style,
            focus_state: selections.focus_state,
            status_badge: selections.status_badge,

            rationale: rationale
                ? rationale.value.trim()
                : ""
        });
    }

    function removePreviewClasses(prefix) {
        if (!preview) return;

        [...preview.classList].forEach(className => {
            if (className.startsWith(prefix)) {
                preview.classList.remove(className);
            }
        });
    }

    function updatePreview(setting, value) {
        if (!preview) return;

        const prefixMap = {
            primary_button: "ui-primary-",
            secondary_button: "ui-secondary-",
            input_style: "ui-input-",
            focus_state: "ui-focus-",
            status_badge: "ui-status-"
        };

        const prefix = prefixMap[setting];

        if (!prefix) return;

        removePreviewClasses(prefix);

        if (setting === "status_badge") {
            if (value === "label_icon") {
                preview.classList.add(
                    "ui-status-label-icon"
                );
            }

            if (value === "label_only") {
                preview.classList.add(
                    "ui-status-label-only"
                );
            }

            if (value === "dot_label") {
                preview.classList.add(
                    "ui-status-dot-label"
                );
            }

            return;
        }

        preview.classList.add(
            `${prefix}${value}`
        );
    }

    document
        .querySelectorAll(".ui-component-option")
        .forEach(button => {

            button.addEventListener("click", () => {
                const setting =
                    button.dataset.setting;

                const value =
                    button.dataset.value;

                if (!setting || !value) {
                    return;
                }

                document
                    .querySelectorAll(
                        `.ui-component-option[data-setting="${setting}"]`
                    )
                    .forEach(item => {
                        item.classList.remove("active");
                    });

                button.classList.add("active");

                selections[setting] = value;

                updatePreview(
                    setting,
                    value
                );

                updateAnswer();

                if (status) {
                    status.textContent =
                        "Component system updated. Continue refining your design.";

                    status.classList.remove(
                        "ui-component-status--error"
                    );
                }
            });
        });

    if (rationale) {
        rationale.addEventListener(
            "input",
            () => {
                if (charCount) {
                    charCount.textContent =
                        `${rationale.value.length} characters`;
                }

                updateAnswer();
            }
        );
    }

    form.addEventListener(
        "submit",
        event => {

            const missingDecision =
                Object.values(
                    selections
                ).some(value => !value);

            if (missingDecision) {
                event.preventDefault();

                if (status) {
                    status.textContent =
                        "Complete all component decisions before continuing.";

                    status.classList.add(
                        "ui-component-status--error"
                    );
                }

                return;
            }

            const rationaleText =
                rationale
                    ? rationale.value.trim()
                    : "";

            if (rationaleText.length < 80) {
                event.preventDefault();

                if (status) {
                    status.textContent =
                        "Explain your component system rationale in at least 80 characters.";

                    status.classList.add(
                        "ui-component-status--error"
                    );
                }

                rationale?.focus();

                return;
            }

            updateAnswer();
        }
    );

    /* Initial preview */
    updatePreview(
        "primary_button",
        selections.primary_button
    );

    updatePreview(
        "secondary_button",
        selections.secondary_button
    );

    updatePreview(
        "input_style",
        selections.input_style
    );

    updatePreview(
        "focus_state",
        selections.focus_state
    );

    updatePreview(
        "status_badge",
        selections.status_badge
    );

    if (charCount) {
        charCount.textContent = "0 characters";
    }

    updateAnswer();
}

if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initUIComponentSystem
    );
} else {
    initUIComponentSystem();
}