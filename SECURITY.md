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
| Site template (supply chain) | Tool repos clone this repo in CI to build their Pages site. A compromised template could inject malicious HTML/JS into all tool repo sites. | Template changes are reviewed before merge. Tool repos pin to `main` branch. The build script does not execute arbitrary code from tool repos -- it only reads JSON and Markdown files. |

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

- Never commit credentials, tokens, API keys, business emails, or local filesystem paths. The `safety-scan` CI job blocks these.
- Do not add external CDN dependencies to the catalog site.
- Do not use `innerHTML`, `outerHTML`, `eval`, or `new Function` with registry or user data. The `safety-scan` job greps for these.
- Review scaffold template changes for potential injection vectors.
- Keep Jinja2 and other dependencies current; address Dependabot PRs within 7 days.
- Pin third-party GitHub Actions by full commit SHA. See [`.github/workflows/README.md`](.github/workflows/README.md).
- Sign off every commit under the DCO. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Related standards

- [`standards/security.md`](standards/security.md) - the ecosystem-wide security standard that applies to every tool repo.
- [`standards/licensing.md`](standards/licensing.md) - inbound/outbound licensing model.
- [`docs/.well-known/security.txt`](docs/.well-known/security.txt) - RFC 9116 machine-readable contact.
