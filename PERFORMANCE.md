# Performance

> Lighthouse audit results for all TMHSDigital developer tool sites.

## Audit Date

2026-04-09 (Lighthouse 12.8.2, Chrome headless)

## Baseline Scores (pre v1.4.0 deploy)

| Site | Performance | Accessibility | Best Practices | SEO |
|------|:-----------:|:-------------:|:--------------:|:---:|
| [Directory Catalog](https://tmhsdigital.github.io/Developer-Tools-Directory/) | 70 | 95 | 96 | 100 |
| [Docker Developer Tools](https://tmhsdigital.github.io/Docker-Developer-Tools/) | 86 | 95 | 100 | 100 |
| [Steam Cursor Plugin](https://tmhsdigital.github.io/Steam-Cursor-Plugin/) | 68 | 95 | 100 | 100 |
| [Monday Cursor Plugin](https://tmhsdigital.github.io/Monday-Cursor-Plugin/) | 84 | 95 | 100 | 100 |
| [Home Lab Developer Tools](https://tmhsdigital.github.io/Home-Lab-Developer-Tools/) | 83 | 95 | 100 | 100 |

## Optimizations Applied (v1.4.0)

### Font Preloading

Added `<link rel="preload">` for Inter Regular and Inter Bold `.woff2` files on both the directory catalog and all tool sites. This eliminates the Flash of Invisible/Unstyled Text (FOIT/FOUT) by signaling the browser to fetch fonts before they are referenced in CSS.

```html
<link rel="preload" as="font" type="font/woff2" crossorigin href="fonts/inter-regular.woff2" />
<link rel="preload" as="font" type="font/woff2" crossorigin href="fonts/inter-bold.woff2" />
```

### OG Meta Tags

Added `og:title`, `og:description`, `og:type`, and `og:image` meta tags to the directory catalog site. Tool sites already had these via the Jinja2 template.

### Existing Optimizations (pre v1.4.0)

- `font-display: swap` on all `@font-face` declarations
- Self-hosted `.woff2` fonts (no CDN dependency)
- Inline CSS and JS (no external stylesheets or scripts to fetch)
- `prefers-reduced-motion` support disabling animations
- Passive event listeners on scroll handlers
- Single HTML file per site (no additional network requests beyond fonts and logo)

## Notes

- Performance scores fluctuate by ~5-10 points between runs due to network variability and GitHub Pages CDN.
- The Directory Catalog score is lower because it has a larger DOM (9 tool cards, standards grid, embedded registry JSON, and search index JSON).
- Steam site's lower performance score is due to its larger page size (30 skills, 25 MCP tools).
- Accessibility at 95 across all sites; the remaining 5 points are typically contrast ratios on dim text and missing landmark roles.

## Re-audit

After deploying v1.4.0, re-run:

```bash
npx lighthouse <url> --output=json --quiet --chrome-flags="--headless"
```
