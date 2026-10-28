# Themes

Customize layout → **Appearance** → **Theme**:

| Theme | Notes |
|---|---|
| Desk (default) | The original Desk look. Nothing changes until you pick another theme. |
| Spring, Summer, Fall, Winter | Each has a light and a dark version and follows the **Light / dark** setting (Match system, Light, Dark). |
| Hacker / Dark | Always dark, green-on-black, monospace. |
| Custom | Colour pickers for Background, Cards, Card border, Accent and (optional) Text. "Auto text color" picks dark or light text for contrast; untick it to choose your own. Live preview while you drag, plus a contrast report (Text, Muted, Accent text, Button). "Reset to" copies any preset into Custom as a starting point. |

Every preset palette (light and dark) passes WCAG AA: 4.5:1 for text, 3:1 for status dots and bars.
Custom derives muted text, hover and status colours from your picks so they stay readable; the accent is yours.

## How it works
- `custom/theme.js` holds the palettes (JSON between `/*PAL_BEGIN*/` and `/*PAL_END*/`), the engine and the picker.
  `build.py` inlines it in `<head>` (`/*__THJS__*/`) so the theme applies before the first paint, with no flash.
- `custom/theme.css` (inlined at `/*__THCSS__*/`) styles the picker and moves hard-coded colours in Desk's panels onto theme variables.
- The choice is saved in `localStorage["desk-pal"]` as `{"id": "classic" (Desk) | "spring" | … | "hacker" | "custom", "custom": {bg, card, bd, acc, fg}}` and,
  if you use the Desk helper, synced across your computers like the other `desk-*` settings.
- An older saved **Accent** colour shows as a Custom theme with that accent the first time you load the new version.

## Adding or editing a palette
1. Edit the JSON in `custom/theme.js`. Each palette needs `bg bg2 card bd fg fg2 mut acc acc-s on-acc track`,
   status dots `c-active c-done c-blocked c-hold` and status pills `p-active|done|blocked|hold` on `p-*-bg`.
2. Run `python3 tools/test_themes.py`. It checks contrast for every preset and for derived Custom palettes, pre-paint
   application, persistence, migration of the old accent, the picker, and that no hard-coded colours remain.

**New panels should use the variables** (`--bg --bg2 --card --bd --fg --fg2 --mut --acc --acc-s --on-acc --track --c-* --p-*`), not hex colours.
If a panel must ship hex colours, add a `:root[data-pal] …` override in `custom/theme.css`.
