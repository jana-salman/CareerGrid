(() => {
  "use strict";
  const overlay = document.getElementById("report-overlay");
  const content = document.getElementById("report-content");
  const close = document.getElementById("report-close");
  if (!overlay || !content || !close) return;

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  const textSection = (title, value) =>
    value ? `<h2>${escapeHtml(title)}</h2><p>${escapeHtml(value)}</p>` : "";
  const listSection = (title, values) => {
    if (!Array.isArray(values) || !values.length) return "";
    const items = values
      .map((value) => `<li>${escapeHtml(value)}</li>`)
      .join("");
    return [
      `<h2>${escapeHtml(title)}</h2>`,
      `<ul class="report-list">${items}</ul>`,
    ].join("");
  };
  const normalize = (record) => {
    const data = record?.data || record?.evaluation || record;
    return data && typeof data === "object" ? data : null;
  };
  const dimensionsMarkup = (evaluation) => {
    const dimensions = Object.entries(evaluation.dimensions || {})
      .filter(([, value]) => value && typeof value === "object")
      .map(([name, value]) => {
        const label = name.replaceAll("_", " ");
        const score = value.score ?? "—";
        const maximum = value.max_score ?? 10;
        const feedback = value.feedback
          ? `<p>${escapeHtml(value.feedback)}</p>`
          : "";
        return [
          '<article class="report-dimension">',
          `<strong>${escapeHtml(label)} · `,
          `${escapeHtml(score)}/${escapeHtml(maximum)}</strong>`,
          feedback,
          "</article>",
        ].join("");
      });
    if (!dimensions.length && Array.isArray(evaluation.step_feedback)) {
      evaluation.step_feedback.forEach((step) => {
        if (!step || typeof step !== "object") return;
        const feedback = step.feedback
          ? `<p>${escapeHtml(step.feedback)}</p>`
          : "";
        dimensions.push(
          [
            '<article class="report-dimension">',
            `<strong>Step ${escapeHtml(step.step)} · `,
            `${escapeHtml(step.score)}/100</strong>`,
            feedback,
            "</article>",
          ].join(""),
        );
      });
    }
    return dimensions.length
      ? `<h2>Performance breakdown</h2><div class="report-grid">${dimensions.join("")}</div>`
      : "";
  };

  window.CareerGridReport = {
    open(record, meta = {}) {
      const evaluation = normalize(record);
      if (!evaluation) {
        content.innerHTML = [
          '<div class="report-kicker">CAREERGRID · TASK REVIEW REPORT</div>',
          `<h1>${escapeHtml(meta.task || "Task Review Report")}</h1>`,
          "<h2>Review unavailable</h2>",
          "<p>The evaluation data for this task could not be loaded. ",
          "Your submitted work remains recorded.</p>",
        ].join("");
      } else {
        const context = [meta.position, meta.company]
          .filter(Boolean)
          .map(escapeHtml)
          .join(" · ");
        const score =
          typeof evaluation.overall_score === "number"
            ? `<div class="report-score">${escapeHtml(evaluation.overall_score)} / 100</div>`
            : "";
        content.innerHTML = [
          '<div class="report-kicker">CAREERGRID · TASK REVIEW REPORT</div>',
          `<h1>${escapeHtml(meta.task || "Task Review")}</h1>`,
          context ? `<p>${context}</p>` : "",
          score,
          textSection("Frontend readiness", evaluation.frontend_readiness),
          textSection("Overall assessment", evaluation.summary),
          dimensionsMarkup(evaluation),
          listSection("Strengths", evaluation.strengths),
          listSection(
            "Areas for improvement",
            evaluation.areas_for_improvement,
          ),
          textSection("Advisor feedback", evaluation.advisor_feedback),
          listSection(
            "Recommended next steps",
            evaluation.recommended_next_steps || evaluation.recommended_skills,
          ),
        ].join("");
      }
      overlay.hidden = false;
      close.focus();
    },
  };
  const closeReport = () => {
    overlay.hidden = true;
  };
  close.addEventListener("click", closeReport);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) closeReport();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !overlay.hidden) closeReport();
  });
})();
