document.body.addEventListener("htmx:afterSwap", (event) => {
  const newContent = event.detail.target;
  newContent.querySelectorAll('.scroll-container').forEach(container => {
    const text = container.querySelector('.scroll-text');
    if (text && text.scrollWidth > container.clientWidth) {
	text.style.animation = 'scroll-left 10s linear infinite';
    } else {
      text.style.animation = '';
    }
  });
});
