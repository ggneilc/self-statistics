document.addEventListener('htmx:afterSwap', (e) => {
  if (e.target.id !== 'graph_display__container') return;

  const container = document.getElementById("d3-calendar");
  const data = JSON.parse(container.dataset.days);

  const width = 399;
  const boxSize = 20;
  const padding = 4;
  

  // Map week numbers to Y positions
  const weeks = [...new Set(data.map(d => d.week))].sort((a, b) => a - b);
  const weekIndex = week => weeks.indexOf(week);
  const rows = 25;
  const cols = 16;

  /* single dim array with double dim indexing */ 
  const cells = Array.from({ length: rows * cols}, (_, index) => {
    const col = index % cols;
    const row = Math.floor(index / cols)
    return {row, col}
  });
  
  // TODO : 
  // place gray tiles to cover entire graph_display__container
  // overlay tiles 


  const svg = d3.select(container)
    .append("svg")
    .attr("width", (boxSize + padding) * cols)
    .attr("height", (boxSize + padding) * rows);

  const bgLayer = svg.append("g").attr("class", "background");
  const fgLayer = svg.append("g").attr("class", "foreground");

bgLayer.selectAll("rect")
  .data(cells)
  .enter()
  .append("rect")
  .attr("x", d => d.col * (boxSize + padding))
  .attr("y", d => d.row * (boxSize + padding))
  .attr("width", boxSize)
  .attr("height", boxSize)
  .style("fill", "#000")
  .style("opacity", 0)
  .transition()
  .duration(300)
  .style("opacity", 1);


  const colorScale = d3.scaleLinear()
    .domain([0, 1])
    .range(["#ff3b3b", "#3bff64"]);

  const rects = fgLayer.selectAll("rect")
    .data(data)
    .enter()
    .append("rect")
    .attr("x", d => d.day * (boxSize + padding))
    .attr("y", d => weekIndex(d.week) * (boxSize + padding))
    .attr("width", boxSize)
    .attr("height", boxSize)
    .attr("fill", d => colorScale(d.ratio))
    .attr("hx-get", d => `/day/${d.id}`)
    .attr("hx-trigger", "click")
    .attr("hx-target", "#graph_display__container")
    .attr("stroke", "#111")
    .style("opacity", 0);  // start invisible

  // Animate opacity + "pop in" scale
  rects.transition()
    .delay((d, i) => i * 10)  // staggered entrance
    .duration(400)
    .style("opacity", 1)
  // .attrTween("transform", function () {
      // little scale animation
 //    return d3.interpolateString("scale(0.5)", "scale(1)");
//    });

  svg.on("mousemove", function (event) {
  const [mx, my] = d3.pointer(event);
  svg.selectAll("rect").each(function () {
    const rect = d3.select(this);
    const x = +rect.attr("x") + boxSize / 2;
    const y = +rect.attr("y") + boxSize / 2;
    const dist = Math.hypot(mx - x, my - y);

    const scale = dist < 20
      ? 1 + (1.15 - 1) * (1 - dist / 50)
      : 1;
    
    const mv = scale > 1
        ? (scale===1.15) ? scale * 4 : scale * 1
        : 0 ;

    rect
      .style("transform-box", "fill-box")
      .style("transform-origin", "center")
      .style("transform", `scale(${scale}) translateY(-${mv}px)`)
      .style("transition", "all 0.1s ease");
    });
    });

    svg.style("overflow", "visible");

    svg.on("mouseleave", () => {
    svg.selectAll("rect").style("transform", "scale(1)");
    });
});



