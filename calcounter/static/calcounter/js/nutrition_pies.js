function drawNutrientPie(selector, data, title, colorScheme) {
    // Fixed internal coordinate system — SVG scales to container via viewBox
    const size = 110;
    const margin = 10;
    const radius = size / 2 - margin;
    const container = d3.select(selector);
    container.selectAll("svg").remove();

    const svgEl = container.append("svg")
        .attr("viewBox", `0 0 ${size} ${size}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "100%");

    const svg = svgEl.append("g")
        .attr("transform", `translate(${size / 2}, ${size / 2})`);

    const color = d3.scaleOrdinal().domain(data.map(d => d.name)).range(colorScheme);
    
    // Custom color for Sugar drill-down (usually a lighter or specific orange/yellow)
    const sugarColor = "var(--sugar-color)"; 

    // Helper to generate the data for the pie
    const pie = d3.pie()
        .value(d => d.ratio !== undefined ? d.ratio : d.value)
        .sort(null);

    const arc = d3.arc()
        .innerRadius(radius * 0.6)
        .outerRadius(radius)
        .cornerRadius(4);

    const arcHover = d3.arc()
        .innerRadius(radius * 0.6)
        .outerRadius(radius * 1.1)
        .cornerRadius(4);

    const centerText = svg.append("text")
        .attr("text-anchor", "middle")
        .style("pointer-events", "none");

    const resetCenter = () => {
        centerText.selectAll("tspan").remove();
        centerText.append("tspan")
            .attr("x", 0).attr("dy", "0.35em")
            .style("font-size", "10px").style("fill", "#999")
            .style("font-weight", "bold").text(title);
    };

function updateCenterText(d, color) {
    centerText.selectAll("tspan").remove();
    
    // Line 1: Name
    centerText.append("tspan")
        .attr("x", 0)
        .attr("dy", "-0.1em")
        .style("font-size", "11px")
        .style("font-weight", "bold")
        .style("fill", d.data.name === "Sugar" ? sugarColor : 
                       d.data.name === "Fiber" ? "var(--fiber-color)" : 
                       color(d.data.name))
        .text(d.data.name);

    // Line 2: Value/Ratio
    const displayVal = d.data.ratio !== undefined 
        ? `${(d.data.ratio * 100).toFixed(0)}%` 
        : `${d.data.value}g`;

    centerText.append("tspan")
        .attr("x", 0)
        .attr("dy", "1.1em")
        .style("font-size", "9px")
        .style("fill", "#fff")
        .text(displayVal);
}


let isAnimating = false; // Global flag to lock interactions

function render(currentData, isDrilldown = false) {
    const filteredData = currentData.filter(d => (d.value || d.ratio) > 0);
    const pieData = pie(filteredData);
    
    const groups = svg.selectAll(".slice-group")
        .data(pieData, d => d.data.name);

    groups.exit().remove();

    const enterGroups = groups.enter()
        .append("g")
        .attr("class", "slice-group");

    enterGroups.append("path");
    enterGroups.append("text");

    const allGroups = enterGroups.merge(groups);

    // 1. Lock interactions and run paths
    isAnimating = true;

    allGroups.select("path")
        .transition().duration(isDrilldown ? 400 : 200)
        .attr("d", arc)
        .attr("fill", d => {
            if (d.data.name === "Sugar") return sugarColor;
            if (d.data.name === "Fiber") return "var(--fiber-color)";
            if (d.data.name === "Starch") return "var(--starch-color"; 
            return color(d.data.name);
        })
        .attr("stroke", "#121212")
        .style("stroke-width", "1px")
        .on("end", () => { isAnimating = false; }); // Unlock when finished

    // 2. Animate labels smoothly
    allGroups.select("text")
        .transition().duration(isDrilldown ? 400 : 200)
        .attr("transform", d => `translate(${arc.centroid(d)})`)
        .style("opacity", isDrilldown ? 1 : 0)
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .style("font-size", "10px")
        .style("font-weight", "bold")
        .style("fill", "white")
        .style("pointer-events", "none")
        .text(d => {
            const val = d.data.value !== undefined ? d.data.value : (d.data.ratio || 0);
            return isDrilldown ? `${val}` : `${val}g`;
        });

    // 3. Conditional Interactions
    allGroups.on("mouseenter", function(event, d) {
        if (isAnimating) return; 

    // 1. Handle Drill-down Trigger
    if (d.data.name === "Carbs" && !isDrilldown) {
        const s = d.data.sugar || 0;
        const f = d.data.fiber || 0;
        const starchVal = Math.max(0, d.data.value - s - f);
        const drillDownData = [
            ...data.filter(item => item.name !== "Carbs"),
            { name: "Starch", value: starchVal },
            { name: "Fiber",  value: f },
            { name: "Sugar",  value: s }
        ];
        
        // Update center to indicate we are entering detail mode
        centerText.selectAll("tspan").remove();
        centerText.append("tspan")
            .attr("x", 0).attr("dy", "0.35em")
            .style("font-size", "9px").style("fill", "#fff").text("CARB DETAIL");

        render(drillDownData, true);
        return;
    }

    // 2. Animate Slice Pop
    d3.select(this).select("path")
        .transition().duration(200)
        .attr("d", arcHover);

    // Ensure label becomes visible on hover (Crucial for Minerals/Vitamins)
    d3.select(this).select("text").transition().duration(200).style("opacity", 1);

    // 3. Update Center Text with the hovered sub-nutrient (Sugar, Fiber, etc.)
    updateCenterText(d, color);
})
    .on("mouseleave", function() {
        if (isAnimating || isDrilldown) return; // Don't reset center if in drilldown mode
        
        d3.select(this).select("path").transition().duration(200).attr("d", arc);
        d3.select(this).select("text").transition().duration(200).style("opacity", 0);
        resetCenter();
    });
}
    // Reset drilldown when mouse leaves the whole SVG
    d3.select(selector).select("svg").on("mouseleave", () => {
        render(data, false);
        resetCenter();
    });

    const filteredInitial = data.filter(d => (d.value || d.ratio) > 0.01);
    resetCenter();
    render(filteredInitial);
}