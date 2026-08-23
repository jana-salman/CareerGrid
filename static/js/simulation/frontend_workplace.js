document.addEventListener("DOMContentLoaded", async () => {
    "use strict";

    const workspace = document.getElementById("careergrid-workspace");
    if (
        !workspace ||
        workspace.dataset.positionId !== "frontend-developer" ||
        !workspace.dataset.attemptId
    ) {
        return;
    }

    const attemptId = workspace.dataset.attemptId;
    const totalSteps = 5;
    const appForStep = {
        1: "mail",
        2: "browser",
        3: "vscode",
        4: "browser",
        5: "github",
    };
    const labels = {
        1: "Triage the production report",
        2: "Investigate across viewports",
        3: "Implement a focused fix",
        4: "Verify behavior and regressions",
        5: "Review, commit, and open a PR",
    };
    let scenario = {};
    let progress = { current_step: 1, responses: {} };

    const escapeHtml = (value) =>
        String(value ?? "").replace(
            /[&<>"']/g,
            (character) =>
                ({
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#39;",
                })[character]
        );

    const textArea = (name, label, value = "") =>
        `<label>${escapeHtml(label)}</label>` +
        `<textarea name="${escapeHtml(name)}" required>` +
        `${escapeHtml(value)}</textarea>`;

    const input = (name, label, value = "") =>
        `<label>${escapeHtml(label)}</label>` +
        `<input name="${escapeHtml(name)}" value="${escapeHtml(value)}" required>`;

    async function request(path, options) {
        const response = await fetch(path, {
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            ...options,
        });
        const body = await response.json();
        if (!response.ok) {
            throw new Error(body.error || "Request failed.");
        }
        return body;
    }

    function openApp(name) {
        document.querySelector(`[data-app="${name}"]`)?.click();
        if (name === "browser") {
            window.setTimeout(
                () => window.CareerGridBrowser?.navigate("careergrid://product"),
                0
            );
        }
    }

    function taskFields(step, prior) {
        if (step === 1) {
            const criticalEmailId =
                prior.selected_email_id ||
                scenario.emails?.find((email) => email.is_critical)?.id ||
                "";
            return (
                input("selected_email_id", "Critical email ID", criticalEmailId) +
                input(
                    "selected_priority",
                    "Priority",
                    prior.selected_priority || "Critical"
                ) +
                input("selected_action", "First action", prior.selected_action) +
                textArea(
                    "written_response",
                    "Reply to the frontend lead",
                    prior.written_response
                )
            );
        }

        if (step === 2) {
            return (
                input(
                    "viewports_tested",
                    "Viewports (comma separated)",
                    prior.viewports_tested?.join(", ") || "Desktop, Mobile"
                ) +
                input(
                    "evidence_opened",
                    "Evidence inspected",
                    prior.evidence_opened?.join(", ") || "Console, Elements"
                ) +
                input(
                    "selected_root_cause",
                    "Root cause",
                    prior.selected_root_cause
                ) +
                textArea(
                    "proposed_next_action",
                    "Proposed next action",
                    prior.proposed_next_action
                ) +
                textArea(
                    "investigation_summary",
                    "Investigation summary",
                    prior.investigation_summary
                )
            );
        }

        if (step === 3) {
            const original =
                scenario.project?.files?.find(
                    (file) => file.path === "product.js"
                )?.content || "";
            return (
                input("files_opened", "Files opened", "product.js") +
                textArea(
                    "product_js",
                    "Updated product.js",
                    prior.changed_files?.["product.js"] || original
                ) +
                textArea(
                    "fix_explanation",
                    "Why this is the smallest safe fix",
                    prior.fix_explanation
                )
            );
        }

        if (step === 4) {
            return (
                input(
                    "commands_run",
                    "Safe commands",
                    prior.commands_run?.join(", ") || "npm test, npm run lint"
                ) +
                input(
                    "tests_performed",
                    "Behavior checks",
                    prior.tests_performed?.join(", ") ||
                        "mouse click, keyboard activation, repeated clicks"
                ) +
                input(
                    "viewport_checks",
                    "Viewports",
                    prior.viewport_checks?.join(", ") || "Desktop, Mobile"
                ) +
                input(
                    "accessibility_checks",
                    "Accessibility checks",
                    prior.accessibility_checks?.join(", ") ||
                        "keyboard activation, focus visibility"
                ) +
                input(
                    "release_decision",
                    "Release decision",
                    prior.release_decision || "Ready if all checks pass"
                )
            );
        }

        return (
            input(
                "reviewed_files",
                "Reviewed changed files",
                prior.reviewed_files?.join(", ") || "product.js"
            ) +
            input("commit_message", "Commit message", prior.commit_message) +
            input("pr_title", "Pull request title", prior.pr_title) +
            textArea(
                "pr_description",
                "Pull request description",
                prior.pr_description
            ) +
            input(
                "testing_checklist",
                "Testing checklist",
                prior.testing_checklist?.join(", ")
            ) +
            input(
                "release_recommendation",
                "Release recommendation",
                prior.release_recommendation
            ) +
            textArea(
                "final_team_message",
                "Final team update",
                prior.final_team_message
            )
        );
    }

    function commaSeparatedValues(form, name) {
        return String(new FormData(form).get(name) || "")
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean);
    }

    function buildPayload(step, form) {
        const data = Object.fromEntries(new FormData(form));

        if (step === 1) {
            return {
                opened_email_ids: [data.selected_email_id],
                selected_email_id: data.selected_email_id,
                selected_priority: data.selected_priority,
                selected_action: data.selected_action,
                written_response: data.written_response,
            };
        }
        if (step === 2) {
            return {
                pages_inspected: ["product"],
                viewports_tested: commaSeparatedValues(form, "viewports_tested"),
                evidence_opened: commaSeparatedValues(form, "evidence_opened"),
                selected_root_cause: data.selected_root_cause,
                proposed_next_action: data.proposed_next_action,
                investigation_summary: data.investigation_summary,
            };
        }
        if (step === 3) {
            return {
                files_opened: commaSeparatedValues(form, "files_opened"),
                changed_files: { "product.js": data.product_js },
                fix_explanation: data.fix_explanation,
            };
        }
        if (step === 4) {
            return {
                commands_run: commaSeparatedValues(form, "commands_run"),
                tests_performed: commaSeparatedValues(form, "tests_performed"),
                viewport_checks: commaSeparatedValues(form, "viewport_checks"),
                accessibility_checks: commaSeparatedValues(
                    form,
                    "accessibility_checks"
                ),
                release_decision: data.release_decision,
            };
        }
        return {
            reviewed_files: commaSeparatedValues(form, "reviewed_files"),
            commit_message: data.commit_message,
            pr_title: data.pr_title,
            pr_description: data.pr_description,
            testing_checklist: commaSeparatedValues(form, "testing_checklist"),
            release_recommendation: data.release_recommendation,
            final_team_message: data.final_team_message,
        };
    }

    function render() {
        document.querySelector(".frontend-task-panel")?.remove();
        const step = Number(progress.current_step || 1);
        const done = progress.status === "completed" || progress.evaluation;
        const panel = document.createElement("aside");
        panel.className = "frontend-task-panel";

        if (done) {
            panel.innerHTML = `
                <h2>Frontend simulation complete</h2>
                <p>${escapeHtml(
                    progress.evaluation?.summary || "Your report is ready."
                )}</p>
                <p class="frontend-task-success">${escapeHtml(
                    progress.evaluation?.frontend_readiness || ""
                )}</p>
                <div class="frontend-task-actions">
                    <button class="frontend-task-submit" data-report>Open report</button>
                    <button class="frontend-task-restart" data-restart>Restart</button>
                </div>`;
        } else {
            const progressBars = Array.from(
                { length: totalSteps },
                (_, index) =>
                    `<span class="${index + 1 <= step ? "done" : ""}"></span>`
            ).join("");
            const priorResponse = progress.responses?.[`step_${step}`] || {};
            panel.innerHTML = `
                <small>FRONTEND WORKPLACE · TASK ${step} OF ${totalSteps}</small>
                <h2>${escapeHtml(labels[step])}</h2>
                <div class="frontend-task-progress">${progressBars}</div>
                <form>
                    ${taskFields(step, priorResponse)}
                    <p class="frontend-task-error" hidden></p>
                    <div class="frontend-task-actions">
                        <button class="frontend-task-submit">Save and continue</button>
                        <button type="button" class="frontend-task-restart" data-restart>Restart</button>
                    </div>
                </form>`;
        }

        workspace.append(panel);
        panel.querySelector("form")?.addEventListener("submit", async (event) => {
            event.preventDefault();
            const error = panel.querySelector(".frontend-task-error");
            try {
                const result = await request(
                    `/api/simulation/attempts/${encodeURIComponent(
                        attemptId
                    )}/frontend/progress`,
                    {
                        method: "POST",
                        body: JSON.stringify({
                            step,
                            response: buildPayload(step, event.currentTarget),
                        }),
                    }
                );
                progress.responses[`step_${step}`] = result.response;
                if (step === 3) {
                    window.CareerGridBrowser?.setFrontendPatched(
                        Object.values(result.response.patch_checks || {}).every(
                            Boolean
                        )
                    );
                }
                if (result.evaluation) {
                    progress.status = "completed";
                    progress.evaluation = result.evaluation;
                } else {
                    progress.current_step = Math.min(totalSteps, step + 1);
                }
                render();
                openApp(appForStep[progress.current_step]);
            } catch (requestError) {
                error.hidden = false;
                error.textContent = requestError.message;
            }
        });

        panel.querySelector("[data-report]")?.addEventListener("click", () =>
            window.CareerGridReport?.open(progress.evaluation, {
                task: "Junior Frontend Developer · Buy Now incident",
                context: scenario.company_name,
            })
        );
        panel
            .querySelector("[data-restart]")
            ?.addEventListener("click", async () => {
                if (
                    !window.confirm(
                        "Start a fresh attempt? Your completed history will remain available."
                    )
                ) {
                    return;
                }
                const result = await request(
                    `/api/simulation/attempts/${encodeURIComponent(
                        attemptId
                    )}/frontend/restart`,
                    { method: "POST", body: "{}" }
                );
                window.location.assign(result.workspace_url);
            });
    }

    try {
        const [attempt, saved] = await Promise.all([
            request(
                `/api/simulation/attempts/${encodeURIComponent(attemptId)}`
            ),
            request(
                `/api/simulation/attempts/${encodeURIComponent(
                    attemptId
                )}/frontend/progress`
            ),
        ]);
        scenario = attempt.public_scenario || {};
        progress = saved;
        const checks = progress.responses?.step_3?.patch_checks || {};
        window.CareerGridBrowser?.setFrontendPatched(
            Object.values(checks).length > 0 &&
                Object.values(checks).every(Boolean)
        );
        render();
        openApp(appForStep[Number(progress.current_step || 1)]);
    } catch (requestError) {
        console.error(requestError);
    }
});
