# PWA & mobile

## Bottom nav visible on mobile

Layout uses the **small viewport height** (`100svh`) and `--visual-viewport-height` (from JS) so the bottom navbar stays in the **visible** area when the browser URL bar is shown. Safe area insets are applied so the nav sits above the system home indicator on iOS.

## Add to Home Screen / standalone (no URL bar)

- **iPhone (Safari):** Use **Add to Home Screen**, then open the app by tapping the **home screen icon** (not from inside Safari). It should open in standalone mode without the URL bar.
- **Android:** For a true standalone experience (no URL bar), use **Chrome** and add to home screen from Chrome, then open via the home screen icon. **Firefox on Android** does not use the web app manifest for standalone; it adds a bookmark that still opens in Firefox with the URL bar.
