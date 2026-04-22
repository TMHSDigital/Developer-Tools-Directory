# Testing

Every tool repo must have a `tests/` directory, a testing framework wired into CI, and a documented minimum bar for "tested". This standard defines what that means by runtime and by tool type.

## Frameworks by runtime

| Runtime | Framework | Install file | CI command |
| --- | --- | --- | --- |
| Python | `pytest` | `requirements-test.txt` | `pytest tests/ -v` |
| Node / TypeScript | `vitest` | `package.json` devDeps | `npm test` |
| Lua (CFX) | `busted` | `rockspec` | `busted tests/` |
| Shell | `bats` | documented in README | `bats tests/` |

Pick one per runtime. Do not mix `jest` and `vitest` in the same repo. Do not add `mocha` or `tap` without updating this standard first.

## Minimum bar

A repo is "tested" when all of the following are true:

| Artifact | Required test |
| --- | --- |
| Every MCP tool (`mcp-tools.json` entry) | One happy-path test that calls the tool and asserts a non-error response |
| Every destructive MCP tool (writes, deletes, exec) | One test asserting the tool refuses without `confirm: true` |
| Every skill (`SKILL.md`) | Frontmatter parses, required fields present |
| Every rule (`.mdc`) | Frontmatter parses, `globs` field is a valid glob |
| Every schema file (`plugin.json`, `site.json`, `mcp-tools.json`) | Validates against its documented schema |

Happy-path MCP tests are allowed to use recorded fixtures (VCR-style) or mocked clients. Live API calls in CI are not required.

## Folder layout

```
tool-repo/
  tests/
    conftest.py              # pytest only
    test_mcp_tools.py        # happy-path + confirm tests
    test_skills.py           # frontmatter and file-existence checks
    test_rules.py
    test_schemas.py
    fixtures/                # recorded responses, sample payloads
  requirements-test.txt      # Python only
```

TypeScript repos mirror this:

```
tool-repo/
  tests/
    mcp-tools.test.ts
    skills.test.ts
    rules.test.ts
    schemas.test.ts
    fixtures/
  vitest.config.ts
```

## Secrets in tests

- Never commit real API keys, tokens, or credentials in fixtures.
- Use `.env.example` to document required variables, never `.env`.
- CI provides test credentials via `secrets` only when absolutely needed. Prefer recorded fixtures.
- Test data should be synthetic. Do not use production data even if anonymized.

## CI wiring

Every repo's `validate.yml` must run the test suite conditionally:

```yaml
- name: Run tests
  if: hashFiles('tests/**') != ''
  run: |
    if [ -f requirements-test.txt ]; then
      pip install -r requirements-test.txt
      pytest tests/ -v
    elif [ -f package.json ]; then
      npm test
    fi
```

Tests are mandatory for tools at `active` status. Tools at `experimental` or `beta` may ship without a full suite, but must add tests before graduating (see [lifecycle.md](lifecycle.md)).

## Coverage

Line coverage is not a required metric. The required metric is **tool coverage**: every MCP tool, skill, and rule has at least one test touching it. CI enforces this by comparing the count in `mcp-tools.json` and the count of test IDs.

Coverage reports (e.g. `pytest --cov`) are encouraged but not gated.

## What not to test

- Third-party libraries (trust their own test suites).
- Upstream API behavior beyond what affects tool correctness.
- Trivial getters, constants, or template rendering with no logic.
- Network layer in unit tests. Use fixtures.

## Fast vs slow tests

- Unit tests must complete in under 30 seconds total.
- Integration tests using fixtures may take longer; mark with `@pytest.mark.integration` or `describe('integration', ...)`.
- CI runs unit + integration on every PR. Live-API smoke tests (if any) run on a scheduled workflow, not on PRs.

## Scaffold output

The [scaffold generator](../scaffold/) emits a `tests/` folder, a framework install file, and a `tests/README.md` pointing to this standard. Repos created before this standard landed should backfill tests before their next minor version bump.
