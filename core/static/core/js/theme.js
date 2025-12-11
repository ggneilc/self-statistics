function attachThemeHandler() {
const root = document.documentElement; // <html> element
  const savedTheme = localStorage.getItem("theme");

  if (savedTheme) {
    root.setAttribute("data-theme", savedTheme);
  }

  document.querySelectorAll("#theme-switcher button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const newTheme = btn.dataset.theme;
      root.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
    });
  });
};

// Run once on initial page load
document.addEventListener('DOMContentLoaded', attachThemeHandler);

// Run again every time HTMX swaps in new content
document.body.addEventListener('htmx:afterSwap', attachThemeHandler);
