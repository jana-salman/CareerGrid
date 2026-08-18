(() => {
    "use strict";
    const reportData = document.getElementById("dashboard-reports");
    let reports = {};
    try {
        reports = JSON.parse(reportData?.textContent || "{}");
    } catch (error) {
        console.warn("Dashboard report history could not be read.", error);
    }

    document.querySelectorAll("[data-report-id]").forEach((button) => {
        button.addEventListener("click", () => {
            const report = reports[button.dataset.reportId];
            if (report) window.CareerGridReport?.open(report.evaluation, report.meta);
        });
    });

    const filters = [...document.querySelectorAll("[data-filter]")];
    const cards = [...document.querySelectorAll(".history-card")];
    const emptyMessage = document.getElementById("filter-empty");
    filters.forEach((button) => {
        button.addEventListener("click", () => {
            const filter = button.dataset.filter;
            let visibleCount = 0;
            filters.forEach((item) => item.classList.toggle("is-active", item === button));
            cards.forEach((card) => {
                const matches = filter === "all" || card.dataset.status === filter
                    || (filter === "in_progress" && card.dataset.status === "generating");
                card.hidden = !matches;
                visibleCount += Number(matches);
            });
            if (emptyMessage) emptyMessage.hidden = visibleCount !== 0;
        });
    });
})();
