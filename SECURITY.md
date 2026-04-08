# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Developer Tools Directory, please report it responsibly via [GitHub private security advisory](https://github.com/TMHSDigital/Developer-Tools-Directory/security/advisories/new).

**Please do not open a public issue for security vulnerabilities.**

## Scope

This repository is a meta-repository containing:

- **Markdown documentation** (standards) - no executable code
- **Python scaffold generator** - generates files on the user's local machine
- **Static HTML/CSS/JS catalog site** - deployed to GitHub Pages
- **JSON registry** - data file consumed by the catalog site

### Threat surface

| Area | Risk | Mitigation |
|------|------|------------|
| Scaffold templates (Jinja2) | Template injection if user-supplied values contain Jinja2 syntax | Input is passed through CLI args, not raw template strings. Jinja2 autoescaping is not enabled because output is not HTML-rendered by the scaffold itself. |
| registry.json | Schema poisoning via malicious PR (fake repo URLs, XSS in description fields) | CI validates schema on every PR. The catalog site renders text content via `textContent`, not `innerHTML`. |
| GitHub Pages site | XSS via registry data rendered in the DOM | Tool descriptions are inserted via `textContent`. No `innerHTML` or `eval` is used with registry data. |
| GitHub Actions workflows | Workflow injection via PR title/body in release-drafter | Release-drafter uses the official action with no custom script interpolation of PR content. |

### Out of scope

- Vulnerabilities in the tool repositories themselves (report to those repos directly)
- Vulnerabilities in Jinja2, GitHub Actions, or other third-party dependencies (report upstream)

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
| < 1.0   | No        |

## Response Timeline

- **Acknowledgment:** Within 48 hours of report
- **Initial assessment:** Within 7 days
- **Fix or mitigation:** Depends on severity, typically within 14 days for critical issues

## Security Best Practices for Contributors

- Never commit credentials, tokens, API keys, or passwords
- Do not add external CDN dependencies to the catalog site
- Do not use `innerHTML` or `eval` with user-supplied or registry data in `docs/script.js`
- Review scaffold template changes for potential injection vectors
- Keep the Jinja2 dependency updated
