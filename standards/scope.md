# Scope

What belongs in the Developer Tools Directory and what does not. Every addition to `registry.json` passes the checklist in this document before merge.

## In scope

A repo qualifies for the directory if **all** of the following are true:

| Criterion | Detail |
| --- | --- |
| Developer-facing | Serves a real developer workflow (coding, deploying, debugging, reviewing, managing infra) |
| Cursor or MCP native | Ships at least one of: a Cursor plugin, an MCP server, a shared site template, or a scaffold |
| Maintained | Has a tagged release in the last 6 months or is explicitly in `experimental` status with an owner |
| Standards-compliant | Passes the checklist in [folder-structure.md](folder-structure.md), [ci-cd.md](ci-cd.md), [plugin-manifest.md](plugin-manifest.md) |
| Public | Source is on GitHub under TMHSDigital or a fork explicitly blessed by maintainers |

## Out of scope

A repo does not qualify if any of the following are true:

| Condition | Example |
| --- | --- |
| Pure SDK wrapper with no skills/rules/MCP tools | A thin TypeScript client for some API with no agent surface |
| Personal script or one-off utility | A bash script that syncs the author's dotfiles |
| Abandoned experiment | A repo with no commits in 12+ months and no owner |
| Non-developer tool | Marketing site, investor deck, unrelated side project |
| Private or internal | Requires access to private infra to be useful |
| Documentation-only | A standards repo without code or configuration (this meta-repo is the single exception) |

## Review checklist

When a PR adds an entry to `registry.json`, the maintainer verifies:

- [ ] The repo exists at the URL given in `repo`.
- [ ] The repo has a `README.md`, `LICENSE`, `AGENTS.md`, and `SECURITY.md`.
- [ ] The repo has at least one skill, rule, or MCP tool (count > 0 in `registry.json` for at least one of `skills`, `rules`, `mcpTools`).
- [ ] The repo has a passing `validate.yml` CI on `main`.
- [ ] The repo's `plugin.json` version matches `registry.json` `version`.
- [ ] The repo's primary language matches `registry.json` `language`.
- [ ] The description in `registry.json` is accurate and under 200 characters.
- [ ] Topics in `registry.json` match the repo's actual GitHub topics within reason.
- [ ] `status` is one of: `experimental`, `beta`, `active`, `maintenance`, `deprecated`, `archived` (see [lifecycle.md](lifecycle.md)).
- [ ] The new entry does not overlap meaningfully with an existing tool (no duplicates of the same API).

## Overlap handling

When two candidate tools cover the same domain (e.g. two Docker tools, two Plaid tools), the maintainer picks one of:

| Resolution | When |
| --- | --- |
| Merge | Tools are clearly complementary; combine into one repo |
| Split by layer | One is the MCP server, the other is the Cursor plugin consuming it (see Steam pattern) |
| Reject the newer entry | Older entry is actively maintained and adequately covers the domain |
| Accept both with a cross-link | Tools address meaningfully different use cases |

The resolution is documented in the PR that added the second tool.

## Scope expansion

This standard can expand. Proposing a new category (e.g. browser automation, IDE themes) requires:

1. A pull request amending this document with the new category defined.
2. A worked example showing what a repo in that category looks like.
3. Maintainer approval.

Do not add entries in a new category before the category is documented.

## Removal

If a registered tool falls out of scope (no longer maintained, scope creep, ownership lost), follow [lifecycle.md](lifecycle.md) to move it to `deprecated` then `archived`. Do not silently remove from `registry.json`; deprecation is a documented transition.
