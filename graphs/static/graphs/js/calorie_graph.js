// Scope these variables so the update function can access them
let updateTimeframe; 

function draw_calorie_graph() {
    const selector = "#d3-double-line";
    const container = document.querySelector(selector);
    if (!container) return;
    const rawData = JSON.parse(container.dataset.days);

    // Setup dimensions - increased bottom margin for legend
    const margin = {top: 30, right: 60, bottom: 65, left: 60},
          width = 600 - margin.left - margin.right,
          height = 200 - margin.top - margin.bottom;

    const svg = d3.select(selector).append("svg")
        .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const parseDate = d3.timeParse("%Y-%m-%d");
    rawData.forEach(d => d.parsedDate = parseDate(d.date));
    rawData.sort((a, b) => a.parsedDate - b.parsedDate);

    // Create persistent Axis Groups
    const xAxisGroup = svg.append("g").attr("transform", `translate(0,${height})`);
    const yAxisLeft = svg.append("g");
    const yAxisRight = svg.append("g").attr("transform", `translate(${width}, 0)`);

	const leftLabel = svg.append("g")
		.attr("transform", "translate(-20, -10)")
		.append("text")
		.attr("text-anchor", "middle")
		.style("fill", "#999")
		.style("font-size", "12px")
		.text("kcal");

	const rightLabel = svg.append("g")
		.attr("transform", `translate(${width+13}, -10)`)
		.append("text")
		.attr("text-anchor", "middle")
		.style("fill", "#999")
		.style("font-size", "12px")
		.text("grams");

    // Shared Scales
    const x = d3.scaleTime().range([0, width]);
    const yCal = d3.scaleLinear().range([height, 0]);
    const yMacro = d3.scaleLinear().range([height, 0]);

    // Line Generators
    const lineCal = d3.line().defined(d => d.calories > 0)
        .x(d => x(d.parsedDate)).y(d => yCal(d.calories));

    const lineMacro = (key) => d3.line().defined(d => d.calories > 0)
        .x(d => x(d.parsedDate)).y(d => yMacro(d[key]));

    // --- Draw Legend (Once) ---
    const legendData = [
        { label: "Calories", color: "var(--calorie-color)", dash: "0", weight: 3 },
        { label: "Protein", color: "var(--protein-color)", dash: "3,3", weight: 2 },
        { label: "Carbs", color: "var(--carb-color)", dash: "3,3", weight: 2 },
        { label: "Fat", color: "var(--fat-color)", dash: "3,3", weight: 2 }
    ];

    const legend = svg.append("g")
        .attr("transform", `translate(${width / 2 - 130}, ${height + 50})`); 

    legendData.forEach((d, i) => {
        const legendItem = legend.append("g")
            .attr("transform", `translate(${i * 70}, 0)`);

        legendItem.append("line")
            .attr("x1", 0).attr("x2", 15)
            .attr("y1", -4).attr("y2", -4)
            .attr("stroke", d.color)
            .attr("stroke-width", d.weight)
            .style("stroke-dasharray", d.dash);

        legendItem.append("text")
            .attr("x", 18)
            .attr("y", 0)
            .style("font-size", "10px")
            .style("fill", "#999")
            .text(d.label);
    });

    // --- Global update function ---
    updateTimeframe = function(days) {
        let filteredData = rawData;
        
        if (days !== 'all') {
            const cutoff = new Date();
            cutoff.setDate(cutoff.getDate() - days);
            filteredData = rawData.filter(d => d.parsedDate >= cutoff);
        }

        // 1. Update Scales
        x.domain(d3.extent(filteredData, d => d.parsedDate));
        yCal.domain([0, d3.max(filteredData, d => d.calories) * 1.1 || 2000]);
        yMacro.domain([0, d3.max(filteredData, d => Math.max(d.protein, d.carbs, d.fat)) * 1.1 || 100]);

        // 2. Transition Axes
        xAxisGroup.transition().duration(750).call(d3.axisBottom(x).ticks(5));
        yAxisLeft.transition().duration(750).call(d3.axisLeft(yCal));
        yAxisRight.transition().duration(750).call(d3.axisRight(yMacro));

        // 3. Render Paths
        const drawPath = (data, selector, generator, color, width, dash = "0") => {
            const path = svg.selectAll(selector).data([data]);
            path.enter().append("path").attr("class", selector.replace('.',''))
                .merge(path)
                .transition().duration(750)
                .attr("fill", "none")
                .attr("stroke", color)
                .attr("stroke-width", width)
                .style("stroke-dasharray", dash)
                .attr("d", generator);
        };

        drawPath(filteredData, ".line-cal", lineCal, "var(--calorie-color)", 3);
        drawPath(filteredData, ".line-prot", lineMacro("protein"), "var(--protein-color)", 1.5, "3,3");
        drawPath(filteredData, ".line-carb", lineMacro("carbs"), "var(--carb-color)", 1.5, "3,3");
        drawPath(filteredData, ".line-fat", lineMacro("fat"), "var(--fat-color)", 1.5, "3,3");

        // 4. Update Gap Shading
        svg.selectAll(".gap-rect").remove();
        filteredData.forEach((d, i) => {
            if (i > 0 && (filteredData[i].calories === 0 || filteredData[i-1].calories === 0)) {
                svg.append("rect")
                    .attr("class", "gap-rect")
                    .attr("x", x(filteredData[i-1].parsedDate))
                    .attr("width", x(filteredData[i].parsedDate) - x(filteredData[i-1].parsedDate))
                    .attr("height", height)
                    .attr("fill", "rgba(255, 255, 255, 0.05)")
                    .lower(); 
            }
        });
    };

    // Initial Load
    updateTimeframe('all');
};

// Initial Load
draw_calorie_graph();