<!-- standards-version: 1.6.3 -->

# Repo with broken standards refs

This repo references standards docs that do not exist in the meta-repo at
the snapshot commit:

- See [the glossary](standards/glossary-that-does-not-exist.md) for
  definitions.
- Also [agent template](standards/agents-template.md) — which DOES exist
  in our fixture meta; this should not be a finding.
- Fragment link: [specific section](standards/glossary-that-does-not-exist.md#acronyms)
  — still broken because the file is missing.

[ref]: standards/another-missing-standard.md
