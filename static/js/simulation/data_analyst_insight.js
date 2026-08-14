(() => {

    function initializeDataAnalystInsight() {

        const workspace =
            document.getElementById(
                "daInsightWorkspace"
            );

        if (!workspace) {
            return;
        }


        const form =
            document.getElementById(
                "dataAnalystInsightForm"
            );

        const hiddenAnswer =
            document.getElementById(
                "dataAnalystInsightAnswer"
            );

        const kpiButtons =
            Array.from(
                document.querySelectorAll(
                    ".da-kpi-btn"
                )
            );

        const regionButtons =
            Array.from(
                document.querySelectorAll(
                    ".da-region-card"
                )
            );

        const insightRadios =
            Array.from(
                document.querySelectorAll(
                    'input[name="primaryInsight"]'
                )
            );

        const evidenceCheckboxes =
            Array.from(
                document.querySelectorAll(
                    'input[name="evidence"]'
                )
            );

        const recommendationSelect =
            document.getElementById(
                "recommendationSelect"
            );

        const summary =
            document.getElementById(
                "analystInsightSummary"
            );

        const summaryCount =
            document.getElementById(
                "insightSummaryCount"
            );

        const kpiView =
            document.getElementById(
                "kpiView"
            );

        const regionDetail =
            document.getElementById(
                "regionDetail"
            );

        const regionInspectionCount =
            document.getElementById(
                "regionInspectionCount"
            );

        const submitButton =
            document.getElementById(
                "submitInsightBtn"
            );


        const inspectedKpis =
            new Set();

        const inspectedRegions =
            new Set();


        const kpiData = {

            revenue: {
                title: "Revenue",
                february: "$16,350",
                march: "$14,750",
                change: "−9.8%",
                interpretation:
                    "Revenue decreased month over month. " +
                    "The overall number alone does not identify the cause."
            },

            orders: {
                title: "Orders",
                february: "31",
                march: "25",
                change: "−19.4%",
                interpretation:
                    "Order volume fell faster than revenue, suggesting " +
                    "average order size increased."
            },

            aov: {
                title: "Average Order Value",
                february: "$527",
                march: "$590",
                change: "+12.0%",
                interpretation:
                    "Average order value increased despite lower total " +
                    "revenue because fewer orders were placed."
            }

        };


        const regionData = {

            north: {
                revenue:
                    "$3,600 vs $3,250 (+10.8%)",

                orders:
                    "5 vs 6 (−16.7%)",

                aov:
                    "$720 vs $542 (+32.8%)",

                detail:
                    "North generated more revenue from fewer orders. " +
                    "The increase is driven by larger order values rather " +
                    "than higher transaction volume."
            },

            south: {
                revenue:
                    "$3,150 vs $3,850 (−18.2%)",

                orders:
                    "6 vs 9 (−33.3%)",

                aov:
                    "$525 vs $428 (+22.7%)",

                detail:
                    "South shows the largest meaningful revenue decline. " +
                    "Order volume fell sharply, while average order value rose."
            },

            east: {
                revenue:
                    "$2,100 vs $2,150 (−2.3%)",

                orders:
                    "4 vs 4 (0%)",

                aov:
                    "$525 vs $538 (−2.4%)",

                detail:
                    "East is broadly stable. Neither revenue nor order " +
                    "volume changed enough to explain the company decline."
            },

            west: {
                revenue:
                    "$3,150 vs $3,100 (+1.6%)",

                orders:
                    "5 vs 5 (0%)",

                aov:
                    "$630 vs $620 (+1.6%)",

                detail:
                    "West is essentially flat and is unlikely to be the " +
                    "primary driver of the month-over-month decline."
            }

        };


        function selectedRadioValue(radios) {

            const selected =
                radios.find(
                    (radio) => radio.checked
                );

            return selected
                ? selected.value
                : "";

        }


        function selectedEvidence() {

            return evidenceCheckboxes
                .filter(
                    (checkbox) =>
                        checkbox.checked
                )
                .map(
                    (checkbox) =>
                        checkbox.value
                );

        }


        function updateSelectionStyles() {

            document
                .querySelectorAll(
                    ".da-insight-option"
                )
                .forEach(
                    (option) => {

                        const input =
                            option.querySelector(
                                'input[type="radio"]'
                            );

                        option.classList.toggle(
                            "is-selected",
                            Boolean(
                                input &&
                                input.checked
                            )
                        );

                    }
                );


            document
                .querySelectorAll(
                    ".da-evidence-option"
                )
                .forEach(
                    (option) => {

                        const input =
                            option.querySelector(
                                'input[type="checkbox"]'
                            );

                        option.classList.toggle(
                            "is-selected",
                            Boolean(
                                input &&
                                input.checked
                            )
                        );

                    }
                );

        }


        function inspectKpi(kpi) {

            const data =
                kpiData[kpi];

            if (!data) {
                return;
            }


            inspectedKpis.add(kpi);


            kpiButtons.forEach(
                (button) => {

                    if (
                        button.dataset.kpi === kpi
                    ) {
                        button.classList.add(
                            "is-inspected"
                        );
                    }

                }
            );


            kpiView.innerHTML = `
                <div class="da-kpi-result">

                    <div>
                        <span>February ${data.title}</span>
                        <strong>${data.february}</strong>
                    </div>

                    <div>
                        <span>March ${data.title}</span>
                        <strong>${data.march}</strong>
                    </div>

                    <div>
                        <span>Month-over-Month</span>
                        <strong>${data.change}</strong>
                    </div>

                </div>

                <p style="margin:14px 0 0; color:#52627b;">
                    ${data.interpretation}
                </p>
            `;


            updateSubmissionState();

        }


        function inspectRegion(region) {

            const data =
                regionData[region];

            if (!data) {
                return;
            }


            inspectedRegions.add(region);


            regionButtons.forEach(
                (button) => {

                    if (
                        button.dataset.region === region
                    ) {
                        button.classList.add(
                            "is-inspected"
                        );
                    }

                }
            );


            regionInspectionCount.textContent =
                `${inspectedRegions.size} / 3 minimum inspected`;


            regionDetail.innerHTML = `
                <strong style="display:block; margin-bottom:8px;">
                    ${region.charAt(0).toUpperCase() + region.slice(1)}
                </strong>

                <div>
                    <strong>Revenue:</strong>
                    ${data.revenue}
                </div>

                <div>
                    <strong>Orders:</strong>
                    ${data.orders}
                </div>

                <div>
                    <strong>Average Order Value:</strong>
                    ${data.aov}
                </div>

                <p style="margin:10px 0 0;">
                    ${data.detail}
                </p>
            `;


            updateSubmissionState();

        }


        function updateSummaryCount() {

            summaryCount.textContent =
                `${summary.value.length} / 1500`;

            updateSubmissionState();

        }


        function updateSubmissionState() {

            const ready =
                inspectedKpis.size === 3 &&
                inspectedRegions.size >= 3 &&
                selectedRadioValue(
                    insightRadios
                ) !== "" &&
                selectedEvidence().length >= 2 &&
                recommendationSelect.value !== "" &&
                summary.value.trim().length >= 60;


            submitButton.disabled =
                !ready;


            submitButton.textContent =
                ready
                    ? "Submit Analysis"
                    : "Complete Analysis";

        }


        function restoreSavedAnswer() {

            const savedValue =
                hiddenAnswer.dataset.savedAnswer;


            if (!savedValue) {

                updateSelectionStyles();
                updateSummaryCount();

                return;

            }


            try {

                const saved =
                    JSON.parse(savedValue);


                const savedKpis =
                    Array.isArray(
                        saved.inspected_kpis
                    )
                        ? saved.inspected_kpis
                        : [];


                savedKpis.forEach(
                    (kpi) => {

                        if (kpiData[kpi]) {

                            inspectedKpis.add(kpi);

                            const button =
                                kpiButtons.find(
                                    (item) =>
                                        item.dataset.kpi === kpi
                                );

                            if (button) {
                                button.classList.add(
                                    "is-inspected"
                                );
                            }

                        }

                    }
                );


                const savedRegions =
                    Array.isArray(
                        saved.inspected_regions
                    )
                        ? saved.inspected_regions
                        : [];


                savedRegions.forEach(
                    (region) => {

                        if (regionData[region]) {

                            inspectedRegions.add(
                                region
                            );

                            const button =
                                regionButtons.find(
                                    (item) =>
                                        item.dataset.region === region
                                );

                            if (button) {
                                button.classList.add(
                                    "is-inspected"
                                );
                            }

                        }

                    }
                );


                regionInspectionCount.textContent =
                    `${inspectedRegions.size} / 3 minimum inspected`;


                insightRadios.forEach(
                    (radio) => {

                        radio.checked =
                            radio.value ===
                            saved.selected_insight;

                    }
                );


                const savedEvidence =
                    Array.isArray(
                        saved.supporting_evidence
                    )
                        ? saved.supporting_evidence
                        : [];


                evidenceCheckboxes.forEach(
                    (checkbox) => {

                        checkbox.checked =
                            savedEvidence.includes(
                                checkbox.value
                            );

                    }
                );


                recommendationSelect.value =
                    saved.recommendation || "";


                summary.value =
                    saved.analyst_summary || "";


            } catch (error) {

                console.warn(
                    "Could not restore Data Analyst insight response."
                );

            }


            updateSelectionStyles();
            updateSummaryCount();
            updateSubmissionState();

        }


        kpiButtons.forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    () => {
                        inspectKpi(
                            button.dataset.kpi
                        );
                    }
                );

            }
        );


        regionButtons.forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    () => {
                        inspectRegion(
                            button.dataset.region
                        );
                    }
                );

            }
        );


        insightRadios.forEach(
            (radio) => {

                radio.addEventListener(
                    "change",
                    () => {
                        updateSelectionStyles();
                        updateSubmissionState();
                    }
                );

            }
        );


        evidenceCheckboxes.forEach(
            (checkbox) => {

                checkbox.addEventListener(
                    "change",
                    () => {
                        updateSelectionStyles();
                        updateSubmissionState();
                    }
                );

            }
        );


        recommendationSelect.addEventListener(
            "change",
            updateSubmissionState
        );


        summary.addEventListener(
            "input",
            updateSummaryCount
        );


        form.addEventListener(
            "submit",
            (event) => {

                if (
                    inspectedKpis.size !== 3 ||
                    inspectedRegions.size < 3 ||
                    !selectedRadioValue(
                        insightRadios
                    ) ||
                    selectedEvidence().length < 2 ||
                    !recommendationSelect.value ||
                    summary.value.trim().length < 60
                ) {

                    event.preventDefault();

                    updateSubmissionState();

                    return;

                }


                const response = {

                    task_type:
                        "data_analyst_insight",

                    issue_id:
                        "DA-2104",

                    inspected_kpis:
                        Array.from(
                            inspectedKpis
                        ),

                    inspected_regions:
                        Array.from(
                            inspectedRegions
                        ),

                    selected_insight:
                        selectedRadioValue(
                            insightRadios
                        ),

                    supporting_evidence:
                        selectedEvidence(),

                    recommendation:
                        recommendationSelect.value,

                    analyst_summary:
                        summary.value.trim()

                };


                hiddenAnswer.value =
                    JSON.stringify(
                        response
                    );

            }
        );


        restoreSavedAnswer();

    }


    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initializeDataAnalystInsight
        );

    } else {

        initializeDataAnalystInsight();

    }

})();