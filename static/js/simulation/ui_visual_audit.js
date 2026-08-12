function initUIVisualAudit() {
    const form = document.getElementById("ui-style-form");
    const answerInput = document.getElementById("ui-style-answer");

    if (!form || !answerInput) return;

    const preview = document.getElementById("ui-style-preview");
    const rationale = document.getElementById("ui-design-rationale");
    const rationaleCount = document.getElementById("ui-rationale-count");
    const status = document.getElementById("ui-style-status");
    const colorName = document.getElementById("ui-preview-color-name");

    const design = {
        task_type: "ui_visual_system",
        issue_id: "UI-3107",
        primary_color: "#316CF4",
        primary_color_name: "Royal Blue",
        typography: "modern",
        radius: "10",
        density: "comfortable",
        card_treatment: "border",
        rationale: ""
    };


    // =========================================================
    // SAVE CURRENT DESIGN TO HIDDEN ANSWER
    // =========================================================

    function updateAnswer() {
        design.rationale = rationale
            ? rationale.value.trim()
            : "";

        answerInput.value = JSON.stringify(design);
    }


    // =========================================================
    // PRIMARY COLOR
    // =========================================================

    document
        .querySelectorAll(".ui-color-choice")
        .forEach(button => {

            const buttonColor = button.dataset.color;

            if (buttonColor) {
                button.style.backgroundColor = buttonColor;
            }

            button.addEventListener("click", () => {

                document
                    .querySelectorAll(".ui-color-choice")
                    .forEach(item => {
                        item.classList.remove("active");
                    });

                button.classList.add("active");

                design.primary_color =
                    button.dataset.color;

                design.primary_color_name =
                    button.dataset.colorName;

                if (colorName) {
                    colorName.textContent =
                        design.primary_color_name;
                }

                if (preview) {
                    preview.style.setProperty(
                        "--ui-primary",
                        design.primary_color
                    );
                }

                updateAnswer();
            });
        });


    // =========================================================
    // TYPOGRAPHY / RADIUS / DENSITY / CARD STYLE
    // =========================================================

    document
        .querySelectorAll(".ui-option")
        .forEach(button => {

            button.addEventListener("click", () => {

                const setting = button.dataset.setting;
                const value = button.dataset.value;

                if (!setting || !value) return;

                document
                    .querySelectorAll(
                        `.ui-option[data-setting="${setting}"]`
                    )
                    .forEach(item => {
                        item.classList.remove("active");
                    });

                button.classList.add("active");


                // -------------------------
                // TYPOGRAPHY
                // -------------------------

                if (setting === "font") {
                    design.typography = value;

                    if (preview) {
                        preview.classList.remove(
                            "ui-font-modern",
                            "ui-font-compact",
                            "ui-font-editorial"
                        );

                        preview.classList.add(
                            `ui-font-${value}`
                        );
                    }
                }


                // -------------------------
                // CORNER RADIUS
                // -------------------------

                if (setting === "radius") {
                    design.radius = value;

                    if (preview) {
                        preview.style.setProperty(
                            "--ui-radius",
                            `${value}px`
                        );
                    }
                }


                // -------------------------
                // SPACING DENSITY
                // -------------------------

                if (setting === "density") {
                    design.density = value;

                    if (preview) {
                        preview.classList.remove(
                            "ui-density-compact",
                            "ui-density-comfortable",
                            "ui-density-spacious"
                        );

                        preview.classList.add(
                            `ui-density-${value}`
                        );
                    }
                }


                // -------------------------
                // CARD TREATMENT
                // -------------------------

                if (setting === "card") {
                    design.card_treatment = value;

                    if (preview) {
                        preview.classList.remove(
                            "ui-card-border",
                            "ui-card-shadow",
                            "ui-card-flat"
                        );

                        preview.classList.add(
                            `ui-card-${value}`
                        );
                    }
                }

                updateAnswer();
            });
        });


    // =========================================================
    // DESIGN RATIONALE
    // =========================================================

    if (rationale) {
        rationale.addEventListener("input", () => {

            const length = rationale.value.length;

            if (rationaleCount) {
                rationaleCount.textContent =
                    `${length} characters`;
            }

            design.rationale =
                rationale.value.trim();

            updateAnswer();
        });
    }


    // =========================================================
    // FORM VALIDATION
    // =========================================================

    form.addEventListener("submit", event => {

        updateAnswer();

        if (!rationale || rationale.value.trim().length < 80) {
            event.preventDefault();

            if (status) {
                status.textContent =
                    "Explain your visual direction in at least 80 characters.";

                status.classList.add(
                    "ui-status--error"
                );
            }

            if (rationale) {
                rationale.focus();
            }

            return;
        }

        if (status) {
            status.textContent =
                "Visual system complete.";

            status.classList.remove(
                "ui-status--error"
            );
        }

        updateAnswer();
    });


    // =========================================================
    // INITIAL PREVIEW STATE
    // =========================================================

    if (preview) {
        preview.style.setProperty(
            "--ui-primary",
            design.primary_color
        );

        preview.style.setProperty(
            "--ui-radius",
            `${design.radius}px`
        );

        preview.classList.add(
            "ui-font-modern",
            "ui-density-comfortable",
            "ui-card-border"
        );
    }

    if (colorName) {
        colorName.textContent =
            design.primary_color_name;
    }

    if (rationaleCount) {
        rationaleCount.textContent =
            "0 characters";
    }

    updateAnswer();
}


if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initUIVisualAudit
    );
} else {
    initUIVisualAudit();
}