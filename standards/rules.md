# Rules

A rule is an `.mdc` file under `rules/<rule-name>.mdc` that applies persistent guidance to an AI agent for a defined scope. Rules differ from skills: skills are invoked on demand, rules apply automatically when their scope matches.

## Folder layout

```
tool-repo/
  rules/
    <tool>-<topic>.mdc
    <tool>-secrets.mdc
```

Every rule file is named `<tool-slug>-<topic>.mdc`. The tool slug is the short identifier for the repo (`docker`, `plaid`, `monday`, `homelab`). Topic is kebab-case and descriptive.

## Required frontmatter

Every `.mdc` file opens with a YAML frontmatter block:

```yaml
---
description: One-line summary of what the rule enforces.
globs:
  - "**/*.ts"
  - "**/*.tsx"
alwaysApply: false
---
```

Required fields:

| Field | Type | Notes |
| --- | --- | --- |
| `description` | string | Under 200 characters, present tense |
| `globs` | string[] | Glob patterns defining the rule's scope |
| `alwaysApply` | bool | `true` only for repo-wide conventions |

Optional fields:

| Field | Type | Notes |
| --- | --- | --- |
| `priority` | int | Higher fires first when multiple rules match |
| `when` | string | Human-readable trigger hint |

## Glob conventions

- Use `**/*.ext` for language-wide rules.
- Use `src/**/*.ts` to scope to a subtree.
- Use `**/*.env*` and `**/secrets/**` for the secrets pattern.
- Do not use `*` at the top level without a directory component - it is surprising in agent contexts.
- Avoid globs that match every file (`**/*`). If the rule truly applies everywhere, set `alwaysApply: true` and leave globs empty.

## Body structure

```markdown
# <Rule Title>

<Overview: what the rule enforces and why.>

## Applies to

- Files matching `globs` above.

## Rules

- Concrete, imperative statements.
- "Do X", "Never Y", "Prefer Z over W".

## Examples

### Good

<code block>

### Bad

<code block with the anti-pattern>
```

## The secrets rule pattern

Every tool repo that handles credentials ships a `<tool>-secrets.mdc` rule. Minimum required content:

```markdown
---
description: Never commit or log secrets; use environment variables and .env.example.
globs:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.yml"
  - "**/*.yaml"
alwaysApply: false
---

# <Tool> Secrets

- Never hardcode API keys, tokens, passwords, or OAuth secrets.
- Load from environment variables only. Document required vars in `.env.example`.
- Never log full secrets, even truncated. Redact to `****` before logging.
- Never include secrets in test fixtures. Use placeholder strings.
- Never include secrets in commit messages, PR descriptions, or issue bodies.
```

Each tool repo expands this with domain-specific guidance (e.g. Plaid client_secret rotation, Docker registry tokens).

## Length

Under 100 lines total. Rules are narrow and enforceable. If a rule needs more context, link to a skill or a section of the tool's README.

## Content rules

- Follow [writing-style.md](writing-style.md).
- No emoji, no marketing language, no placeholder "TODO" lines in committed rules.
- Every concrete rule should be either testable or enforceable by review.

## Relationship to `plugin.json`

Every rule path in `.cursor-plugin/plugin.json` `rules` array must point to a real `.mdc` file with valid frontmatter. The `validate.yml` workflow enforces this.

## Testing

Every rule is covered by one frontmatter-validation test (see [testing.md](testing.md)):

- Frontmatter parses as YAML
- `description` and `globs` present
- Each glob is a syntactically valid glob string
- `alwaysApply` is a boolean
