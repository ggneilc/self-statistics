function attachThemeHandler() {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("theme") || "dark";

  // Map theme names to Pico CSS files
  const themeMap = {
    'dark': 'pico.amber.min.css',
    'light': 'pico.amber.min.css',
    'midnight': 'pico.blue.min.css',
    'dracula': 'pico.purple.min.css',
    'nord': 'pico.cyan.min.css',
    'gruvbox-dark': 'pico.orange.min.css',
    'catppuccin-mocha': 'pico.pink.min.css',
    'github-dark': 'pico.slate.min.css'
  };

  // Function to load theme stylesheet
  const loadTheme = (theme) => {
    const picoLink = document.querySelector('link[href*="picocss"]');
    if (picoLink) {
      const cssFile = themeMap[theme] || themeMap['dark'];
      picoLink.href = `https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/${cssFile}`;
    }
    // Always use dark mode, only color scheme changes
    root.setAttribute("data-theme", theme === 'light' ? 'light' : 'dark');
  };

  // Apply saved theme
  loadTheme(savedTheme);

  // Update button active states
  const updateActiveTheme = (currentTheme) => {
    document.querySelectorAll("#theme-switcher button").forEach((btn) => {
      if (btn.dataset.theme === currentTheme) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  };

  // Set initial active state
  updateActiveTheme(savedTheme);

  // Add click handlers
  document.querySelectorAll("#theme-switcher button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const newTheme = btn.dataset.theme;
      loadTheme(newTheme);
      localStorage.setItem("theme", newTheme);
      updateActiveTheme(newTheme);
    });
  });
};

// Run once on initial page load and set up HTMX listener
document.addEventListener('DOMContentLoaded', () => {
  attachThemeHandler();
  // Run again every time HTMX swaps in new content
  document.body.addEventListener('htmx:afterSwap', attachThemeHandler);
});
