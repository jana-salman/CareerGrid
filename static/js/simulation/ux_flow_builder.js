document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ux-flow-form");
    const answerInput = document.getElementById("ux-flow-answer");
    const optionButtons = document.querySelectorAll(".ux-flow-option");
    const selectedFlowContainer = document.getElementById("ux-selected-flow");
    const resetButton = document.getElementById("ux-reset-flow");
    const testButton = document.getElementById("ux-test-flow");
    const statusBox = document.getElementById("ux-flow-status");
    const reasoningInput = document.getElementById("ux-flow-reasoning");
    const submitButton = document.getElementById("ux-flow-submit");

    if (!form || !answerInput || !selectedFlowContainer) {
        return;
    }

    const flow = [];

    let flowTestRuns = 0;
    let hintsUsed = 0;


    function labelForStep(step) {
        const labels = {
            cart: "Cart",
            shipping: "Shipping",
            guest_checkout: "Guest Checkout",
            sign_in: "Sign In",
            create_account: "Create Account",
            payment: "Payment",
            confirmation: "Confirmation",
            newsletter: "Newsletter Signup"
        };

        return labels[step] || step;
    }


    function updateAnswer() {
        const response = {
            task_type: "ux_flow_builder",
            issue_id: "UX-2048",
            selected_flow: [...flow],
            removed_steps: [],
            flow_test_runs: flowTestRuns,
            hints_used: hintsUsed,
            design_reasoning: reasoningInput
                ? reasoningInput.value.trim()
                : ""
        };

        answerInput.value = JSON.stringify(response);
    }


    function renderFlow() {
        selectedFlowContainer.innerHTML = "";

        if (flow.length === 0) {
            const empty = document.createElement("p");
            empty.className = "ux-empty-flow";
            empty.textContent = "Add steps to build your checkout flow.";
            selectedFlowContainer.appendChild(empty);
            updateAnswer();
            return;
        }

        flow.forEach((step, index) => {
            const wrapper = document.createElement("div");
            wrapper.className = "ux-selected-flow-step";

            const label = document.createElement("span");
            label.textContent = labelForStep(step);

            const controls = document.createElement("div");
            controls.className = "ux-flow-step-controls";

            const moveUp = document.createElement("button");
            moveUp.type = "button";
            moveUp.textContent = "↑";
            moveUp.title = "Move step earlier";

            moveUp.addEventListener("click", () => {
                if (index <= 0) {
                    return;
                }

                const previous = flow[index - 1];
                flow[index - 1] = flow[index];
                flow[index] = previous;

                renderFlow();
            });

            const moveDown = document.createElement("button");
            moveDown.type = "button";
            moveDown.textContent = "↓";
            moveDown.title = "Move step later";

            moveDown.addEventListener("click", () => {
                if (index >= flow.length - 1) {
                    return;
                }

                const next = flow[index + 1];
                flow[index + 1] = flow[index];
                flow[index] = next;

                renderFlow();
            });

            const remove = document.createElement("button");
            remove.type = "button";
            remove.textContent = "×";
            remove.title = "Remove step";

            remove.addEventListener("click", () => {
                flow.splice(index, 1);
                renderFlow();
            });

            controls.appendChild(moveUp);
            controls.appendChild(moveDown);
            controls.appendChild(remove);

            wrapper.appendChild(label);
            wrapper.appendChild(controls);

            selectedFlowContainer.appendChild(wrapper);

            if (index < flow.length - 1) {
                const arrow = document.createElement("div");
                arrow.className = "ux-selected-flow-arrow";
                arrow.textContent = "↓";
                selectedFlowContainer.appendChild(arrow);
            }
        });

        updateAnswer();
    }


    function setStatus(message, type = "neutral") {
        if (!statusBox) {
            return;
        }

        statusBox.textContent = message;

        statusBox.classList.remove(
            "ux-status--success",
            "ux-status--warning",
            "ux-status--error"
        );

        if (type === "success") {
            statusBox.classList.add("ux-status--success");
        }

        if (type === "warning") {
            statusBox.classList.add("ux-status--warning");
        }

        if (type === "error") {
            statusBox.classList.add("ux-status--error");
        }
    }


    optionButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const step = button.dataset.step;

            if (!step) {
                return;
            }

            if (flow.includes(step)) {
                setStatus(
                    `${labelForStep(step)} is already in your flow.`,
                    "warning"
                );
                return;
            }

            flow.push(step);
            renderFlow();
        });
    });


    if (resetButton) {
        resetButton.addEventListener("click", () => {
            flow.splice(0, flow.length);
            renderFlow();

            setStatus(
                "Flow reset. Build a new checkout path."
            );
        });
    }


    if (testButton) {
        testButton.addEventListener("click", () => {
            flowTestRuns += 1;

            if (flow.length < 4) {
                setStatus(
                    "Your flow is too short. Include the core checkout stages.",
                    "warning"
                );
                updateAnswer();
                return;
            }

            if (flow[0] !== "cart") {
                setStatus(
                    "A checkout flow should begin with the cart.",
                    "warning"
                );
                updateAnswer();
                return;
            }

            if (!flow.includes("shipping")) {
                setStatus(
                    "The flow is missing shipping information.",
                    "warning"
                );
                updateAnswer();
                return;
            }

            if (!flow.includes("payment")) {
                setStatus(
                    "The flow is missing payment.",
                    "warning"
                );
                updateAnswer();
                return;
            }

            if (!flow.includes("confirmation")) {
                setStatus(
                    "The flow is missing order confirmation.",
                    "warning"
                );
                updateAnswer();
                return;
            }

            if (
                flow.includes("create_account")
                && !flow.includes("guest_checkout")
            ) {
                setStatus(
                    "This still forces account creation. The research showed users need a guest checkout path.",
                    "warning"
                );
                updateAnswer();
                return;
            }

            const paymentIndex = flow.indexOf("payment");
            const confirmationIndex = flow.indexOf("confirmation");

            if (confirmationIndex < paymentIndex) {
                setStatus(
                    "Order confirmation should come after payment.",
                    "warning"
                );
                updateAnswer();
                return;
            }

            if (flow.includes("newsletter")) {
                const newsletterIndex = flow.indexOf("newsletter");

                if (newsletterIndex < confirmationIndex) {
                    setStatus(
                        "Newsletter signup should not interrupt the main checkout path.",
                        "warning"
                    );
                    updateAnswer();
                    return;
                }
            }

            setStatus(
                "Your redesigned checkout flow addresses the main research finding and preserves the essential checkout stages.",
                "success"
            );

            updateAnswer();
        });
    }


    if (reasoningInput) {
        reasoningInput.addEventListener("input", updateAnswer);
    }


    function restoreSavedAnswer() {
        const savedValue = answerInput.dataset.savedAnswer;

        if (!savedValue) {
            updateAnswer();
            return;
        }

        try {
            const saved = JSON.parse(savedValue);

            if (Array.isArray(saved.selected_flow)) {
                saved.selected_flow.forEach((step) => {
                    if (!flow.includes(step)) {
                        flow.push(step);
                    }
                });
            }

            if (
                reasoningInput
                && saved.design_reasoning
            ) {
                reasoningInput.value = saved.design_reasoning;
            }

            flowTestRuns = Number(saved.flow_test_runs || 0);
            hintsUsed = Number(saved.hints_used || 0);

            renderFlow();

        } catch (error) {
            console.warn(
                "Could not restore UX flow response.",
                error
            );

            updateAnswer();
        }
    }


    form.addEventListener("submit", (event) => {
        const reasoning = reasoningInput
            ? reasoningInput.value.trim()
            : "";

        if (flow.length < 4) {
            event.preventDefault();

            setStatus(
                "Build a complete checkout flow before continuing.",
                "error"
            );

            return;
        }

        if (!flow.includes("guest_checkout")) {
            event.preventDefault();

            setStatus(
                "Your redesigned flow must address the research finding by providing a guest checkout option.",
                "error"
            );

            return;
        }

        if (!flow.includes("payment")) {
            event.preventDefault();

            setStatus(
                "Your flow must include payment.",
                "error"
            );

            return;
        }

        if (!flow.includes("confirmation")) {
            event.preventDefault();

            setStatus(
                "Your flow must include order confirmation.",
                "error"
            );

            return;
        }

        if (flowTestRuns < 1) {
            event.preventDefault();

            setStatus(
                "Test your redesigned flow before continuing.",
                "error"
            );

            return;
        }

        if (reasoning.length < 20) {
            event.preventDefault();

            setStatus(
                "Explain your design reasoning before continuing.",
                "error"
            );

            if (reasoningInput) {
                reasoningInput.focus();
            }

            return;
        }

        updateAnswer();

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Saving flow...";
        }
    });


    restoreSavedAnswer();
});