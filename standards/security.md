# Security

Every TMHSDigital developer tool repo follows this security standard: vulnerability disclosure, secrets handling, dependency hygiene, and required `SECURITY.md` content.

## `SECURITY.md` required content

Every repo ships a `SECURITY.md` at the root. It must contain:

| Section | Content |
| --- | --- |
| Reporting a vulnerability | Link to the GitHub Security Advisory form for that repo |
| Scope | What the repo contains and where the threat surface is |
| Out of scope | What the repo does not cover (e.g. upstream deps, unrelated repos) |
| Supported versions | Table of versions receiving security fixes |
| Response timeline | Acknowledgment, assessment, and fix SLAs |

A baseline template is shipped by the scaffold generator. Repos may expand it; they may not reduce it below the required sections.

## Vulnerability disclosure

- All reports go through GitHub Security Advisories, not public issues, email, or chat.
- Acknowledgment within 48 hours of report receipt.
- Initial assessment within 7 days.
- Fix or documented mitigation within 14 days for critical severity, 30 days for high, best-effort for medium/low.
- Credit the reporter in the advisory unless they request otherwise.
- CVE request where appropriate.

## Secrets handling

Secrets never enter the repo. This rule has no exceptions.

| Artifact | What it holds |
| --- | --- |
| `.env` | Gitignored. Real local credentials only |
| `.env.example` | Committed. Shows required variable names with placeholder values |
| Fixtures | Synthetic data only. No production data, even anonymized |
| CI logs | Secrets are masked by GitHub Actions when added via `secrets` |

### Hard rules

- Never commit an `.env`, `secrets.json`, `*.pem`, `*.key`, `*.p12`, or any credential file.
- Never hardcode API keys, tokens, passwords, OAuth client secrets, or private keys in source.
- Never log full secrets. Redact to `****` or the last 4 characters.
- Never include secrets in error messages returned from MCP tools.
- Never paste secrets in issues, PRs, commit messages, or comments.

### Enforcement

- `.gitignore` blocks the common patterns (see [folder-structure.md](folder-structure.md)).
- CI's credential-scan step greps for common credential strings on every PR.
- `codeql.yml` runs weekly security scanning.
- Every tool repo ships a `<tool>-secrets.mdc` rule (see [rules.md](rules.md)).

## Dependency hygiene

- `dependency-review.yml` runs on every PR and fails on high-severity vulnerabilities.
- Pin direct dependencies to a minor version: `Jinja2>=3.1,<4.0`.
- Do not pin transitive dependencies unless a vulnerability forces it.
- Review Dependabot PRs within 7 days.
- Remove unused dependencies promptly.

## GitHub Actions supply chain

- Pin third-party actions by full commit SHA, not tag: `actions/checkout@<sha>`.
- GitHub-published actions (`actions/`, `github/`) may use major-version tags (`@v4`).
- Set `permissions: {}` at the workflow top, grant per-job only what is needed.
- Never use `pull_request_target` with a checkout of PR code.
- Never run `eval`, `bash -c "${{ github.event.* }}"`, or any untrusted event data in a shell context.

Convention documented in `.github/workflows/README.md`.

## Catalog site (directory repo)

The directory's `docs/` site has stricter rules because it deploys publicly:

- No external CDN dependencies.
- No `innerHTML`, `outerHTML`, `eval`, or `new Function` with registry or user data.
- All text from `registry.json` renders via `textContent`.
- A CI grep gate fails the build if `innerHTML` / `eval` is reintroduced.

## Tool-repo docs sites

Tool repos built via `site-template/build_site.py` inherit the same rules:

- No external CDN beyond self-hosted fonts.
- Data from repo files is rendered as text, not HTML.
- Markdown is parsed by a vetted library, not `innerHTML`.

## Contributor security hygiene

- Commits must be signed via DCO (see [licensing.md](licensing.md)). The GitHub DCO App enforces this.
- Branch protection on `main` requires PR review, passing CI, and no force pushes.
- Maintainers use 2FA on their GitHub accounts. Organizations enforce this at the org level.

## Reporting process summary

```
1. Discover vulnerability
2. Open a GitHub Security Advisory on the affected repo
3. Maintainer acknowledges within 48 hours
4. Triage and CVE request if warranted
5. Private fork, patch, reviewed by at least one other maintainer
6. Coordinated release + published advisory
7. Credit reporter in advisory
```

## Out of scope

- Vulnerabilities in upstream dependencies (report to those projects).
- Vulnerabilities in GitHub, Cursor, or the MCP specification itself.
- Self-inflicted misconfiguration by users running tools with their own credentials on their own infrastructure.
