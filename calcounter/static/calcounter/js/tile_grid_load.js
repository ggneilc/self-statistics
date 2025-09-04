document.addEventListener('htmx:afterSwap', (e) => {
  if (e.target.id !== 'graph_display__container') return;

  const container = document.getElementById("d3-tile");
//  const data = JSON.parse(container.dataset.days);

  const boxSize = 20;
  const padding = 4;

  const rows = 19;
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


  svg.selectAll("rect")
    .data(cells)
    .enter()
    .append("rect")
    .attr("x", d => d.col * (boxSize + padding))
    .attr("y", d => d.row * (boxSize + padding))
    .attr("width", boxSize)
    .attr("height", boxSize)
    .stroke("#888")
});