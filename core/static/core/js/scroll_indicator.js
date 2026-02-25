function initScrollIndicators() {
    const col = document.querySelector('.dashboard-columns');
    const bar = document.getElementById('scroll-indicators');
    if (!col || !bar) return;

    // Build one dot per column
    const count = col.children.length;
    bar.innerHTML = Array.from({ length: count }, (_, i) =>
        `<span class="scroll-dot" data-index="${i}"></span>`
    ).join('');

    // Set first dot active
    bar.querySelector('.scroll-dot').classList.add('active');

    // Update active dot as user swipes
    col.addEventListener('scroll', () => {
        const index = Math.round(col.scrollLeft / col.clientWidth);
        bar.querySelectorAll('.scroll-dot').forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
    });
}

// Re-run whenever HTMX swaps a new dashboard into #content
document.body.addEventListener('htmx:afterSwap', (e) => {
    if (e.detail.target.id === 'content') initScrollIndicators();
});

// On initial page load, wait for HTMX to finish rendering before initializing
document.body.addEventListener('htmx:load', () => {
    if (document.querySelector('.dashboard-columns')) initScrollIndicators();
}, { once: true });