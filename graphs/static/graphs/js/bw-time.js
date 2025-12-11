document.addEventListener("DOMContentLoaded", () => {
  // Function to render the chart
  function renderBWGraph() {
    const container = document.getElementById("d3-line");
    if (!container) return; // No graph container, nothing to do

    // Parse data from data-days attribute
    let data;
    try {
      data = JSON.parse(container.dataset.days);
    } catch (err) {
      console.error("Invalid day data:", err);
      return;
    }

    // Parse dates and sort
    data = data.map(d => ({
      date: new Date(d.day),
      value: +d.value,
      ma7: +d.ma7
    })).sort((a, b) => a.date - b.date);

    // Remove any previous SVG if re-rendering
    container.innerHTML = "";

    // --- Setup chart dimensions ---
    const margin = { top: 20, right: 30, bottom: 30, left: 50 };
    const width = container.clientWidth || 400;
    const height = 250;

    // --- Create scales ---
    const x = d3.scaleTime()
      .domain(d3.extent(data, d => d.date))
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain([d3.min(data, d => d.value) - 1,
               d3.max(data, d => d.value) + 1])
      .nice()
      .range([height - margin.bottom, margin.top]);

    // --- Create SVG ---
    const svg = d3.select(container)
      .append("svg")
      .attr("width", width)
      .attr("height", height);

    // --- X Axis ---
    svg.append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat(d3.timeFormat("%b %d")))
      .selectAll("text")
      .style("font-size", "0.8rem")
      .style("fill", "var(--text, #f5f5f5)");

    // --- Y Axis ---
    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5))
      .selectAll("text")
      .style("font-size", "0.8rem")
      .style("fill", "var(--text, #f5f5f5)");

    // --- Line Generator ---
    const line = d3.line()
      .x(d => x(d.date))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX);

    const maline = d3.line()
	.x(d => x(d.date))
	.y(d => y(d.ma7))
	.curve(d3.curveBasis);

    // --- Draw Line ---
    svg.append("path")
      .datum(data)
      .attr("fill", "none") .attr("stroke", "var(--accent, #ffc83d)")
      .attr("stroke-width", 2)
      .attr("d", line);
    const path = svg.append("path")
      .datum(data)
      .attr("fill", "none") .attr("stroke", "var(--blue, #ffc83d)")
      .attr("stroke-width", 2)
      .attr("d", maline);
// Animation
const totalLength = path.node().getTotalLength();

path
    .attr("stroke-dasharray", totalLength + " " + totalLength)
    .attr("stroke-dashoffset", totalLength)
    .transition()
    .duration(2000)
    .ease(d3.easeLinear)
    .attr("stroke-dashoffset", 0);

    // --- Draw Points ---
    svg.selectAll(".dot")
      .data(data)
      .enter()
      .append("circle")
      .attr("class", "dot")
      .attr("cx", d => x(d.date))
      .attr("cy", d => y(d.value))
      .attr("fill", "var(--accent, #ffc83d)")
.transition()
    .delay((d, i) => i * 30)
    .duration(500)
    .attr("r", 3);
  }

  // Run on initial load
  renderBWGraph();

  // Optional: re-render whenever HTMX swaps #graph_display__container
  document.body.addEventListener("htmx:afterSwap", (evt) => {
    if (evt.target.id === "graph-container" || evt.target.id === "graph-controls") {
      renderBWGraph();
    }
  });
});
