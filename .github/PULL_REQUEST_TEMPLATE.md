# Pull Request

## Summary

<!-- One or two sentences on what changes and why. -->

## Type of change

- [ ] `feat` - new standard, new tool in registry, new automation
- [ ] `fix` - correction to existing content, schema, or workflow
- [ ] `docs` - docs-only edit
- [ ] `chore` - infra, dependency bump, cleanup
- [ ] `refactor` - structural change with no functional effect

## Registry impact

- [ ] This PR changes `registry.json`
- [ ] Ran `python scripts/sync_from_registry.py` and committed the regenerated artifacts
- [ ] `python scripts/sync_from_registry.py --check` exits 0 locally

## Standards impact

- [ ] This PR adds or modifies a file in `standards/`
- [ ] Updated both `standards/README.md` and the main `README.md` standards table
- [ ] If the change affects scaffold output, updated the corresponding template in `scaffold/templates/`

## Safety

- [ ] No business emails, real names, or local filesystem paths introduced
- [ ] No credentials, API keys, `.env`, `*.pem`, or `*.key` files committed
- [ ] No `innerHTML`, `eval`, or `new Function` with registry or user data added to `docs/`
- [ ] Third-party GitHub Actions pinned by full commit SHA

## DCO

- [ ] Every commit has a `Signed-off-by:` trailer (see [CONTRIBUTING.md](../CONTRIBUTING.md))

## Linked issues

<!-- e.g. Closes #123 -->
