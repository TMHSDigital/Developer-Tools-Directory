# Licensing

Every TMHSDigital developer tool repo uses CC-BY-NC-ND-4.0 as its outbound license. Contributions are accepted inbound under a broader grant via the Developer Certificate of Origin (DCO). This standard documents the contribution licensing model and how to enforce it.

## The model

| Direction | Terms |
| --- | --- |
| Outbound (what users receive) | CC-BY-NC-ND-4.0 |
| Inbound (what contributors grant) | Broad perpetual license to TMHSDigital (see grant text below) |

CC-BY-NC-ND-4.0 forbids derivatives. Every pull request is literally a derivative. The inbound grant resolves this: contributors grant the project a separate, broader license so the project can accept, modify, and redistribute the contribution under CC-BY-NC-ND-4.0 or any successor license.

This is the same shape as Creative Commons' own "CLA-by-DCO" pattern and similar to the GNU "asymmetric license" pattern.

## Required grant text

Every `CONTRIBUTING.md` contains this paragraph verbatim:

> By submitting a contribution to this repository, you certify that you have the right to do so under the Developer Certificate of Origin (DCO) 1.1, and you grant TMHSDigital a perpetual, worldwide, non-exclusive, royalty-free, irrevocable license to use, reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute your contribution under the project's current license (CC-BY-NC-ND-4.0) or any successor license chosen by the project.

## DCO enforcement

Every commit in a pull request must have a `Signed-off-by:` trailer matching the commit author:

```
Signed-off-by: Jane Developer <jane@example.com>
```

Signing is done at commit time:

```bash
git commit -s -m "feat: add new skill"
```

### Enforcement mechanism

Preferred: the built-in **GitHub DCO App** (a GitHub-maintained App enabled from repo settings). No workflow needed, no self-hosted action, no third-party code runs on PRs.

Fallback: `tim-actions/dco` pinned by full commit SHA with `permissions: { pull-requests: read }`. Only used if the DCO App is unavailable.

Never use unpinned or unaudited third-party DCO actions.

## Why not just relicense to MIT or Apache-2.0?

Considered and rejected. CC-BY-NC-ND-4.0 is chosen deliberately:

- NC (non-commercial) prevents white-label commercial reuse of the standards, prose, and catalog site.
- ND (no derivatives) prevents fragmented forks from claiming to be "the TMHSDigital standards".
- The inbound DCO grant removes the contribution paradox while keeping outbound terms strict.

Tool repos that want permissive code licensing (e.g. an MCP server to be embedded in downstream products) may ship code under MIT or Apache-2.0 while keeping prose and brand assets under CC-BY-NC-ND-4.0. This is documented per-repo in its own `LICENSE` file and `README.md`.

## `LICENSE` file header

Every repo's `LICENSE` file opens with this note:

```
Outbound license: CC-BY-NC-ND-4.0 (see below).
Inbound contribution grant: see CONTRIBUTING.md for the DCO + inbound license grant.
The "inbound = outbound" pattern does not apply because outbound terms forbid derivatives; inbound terms must be broader to allow the project to accept pull requests.
```

## Applying to tool repos

When creating a new tool via the scaffold, the default license is CC-BY-NC-ND-4.0. Pass `--license mit` or `--license apache-2.0` to override for code-heavy repos. Whichever license is chosen:

- `LICENSE` contains the full text.
- `CONTRIBUTING.md` contains the inbound grant paragraph.
- `registry.json` `license` field records the SPDX identifier.
- DCO App is enabled on the repo.

## Per-file license headers

Not required. The repo-level `LICENSE` governs all files unless a file is from a third party, in which case its original header is preserved and noted in `NOTICE.md`.

## Third-party code

If a repo vendors third-party code:

- Keep the original license header intact.
- Add the dependency to a `NOTICE.md` file listing vendor, version, license, and upstream URL.
- Do not mix GPL-family code into any repo. Incompatible with CC-BY-NC-ND-4.0 outbound terms.
