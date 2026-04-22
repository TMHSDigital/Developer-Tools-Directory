# Writing Style

Prose conventions for all TMHSDigital developer tool repos: READMEs, standards docs, skills, rules, inline comments, commit messages, and release notes.

## Punctuation

- No em dashes or en dashes. Use a regular hyphen, comma, parentheses, or a new sentence.
- No "smart quotes". Use straight ASCII quotes.
- No ellipses (`...`). If a sentence trails off, rewrite it.
- One space after a period, not two.

## Structure

- Every Markdown file opens with an H1 title.
- Follow the H1 with a single overview sentence or short paragraph that explains what the document is for.
- Use H2 for major sections, H3 for subsections. Avoid H4 and deeper.
- Tables over bulleted key-value lists for anything with two or more columns of data.
- Code blocks declare a language (` ```bash `, ` ```python `, ` ```yaml `).

## Voice

- Second person ("you") for instructions. First person plural ("we") is acceptable for design rationale.
- Imperative mood for steps: "Add the entry", not "You should add the entry".
- Present tense. Avoid "will" when describing current behavior.
- No marketing language: no "blazing fast", "revolutionary", "seamlessly", "world-class".
- No filler phrases: "in order to", "at the end of the day", "it's worth noting that".

## No emoji

No emoji in any prose, heading, table cell, commit message, release note, skill, rule, or README. The only acceptable image content is SVG badges and the repo logo.

Rationale: emoji render inconsistently across platforms, screen readers, and terminals. Prose should stand on its own without decoration.

## No LLM tells

Avoid phrases that signal AI-generated text:

- "Certainly!", "Of course!", "Absolutely!"
- "I hope this helps"
- "As an AI..." or "As a language model..."
- "delve into", "navigate the landscape of", "in the realm of"
- Excessive disclaimers ("It is important to note that...")
- Bulleted lists that restate the same idea three ways

If a sentence could be deleted without losing information, delete it.

## Length

- READMEs: aim for under 300 lines. Push detail into linked docs.
- Standards: aim for under 200 lines each.
- Skills (`SKILL.md`): under 250 lines. Progressive disclosure via linked support files if more is needed.
- Rules (`.mdc`): under 100 lines.
- Commit messages: 72 characters or less for the subject line, wrapped body if used.

## Links

- Prefer relative links inside the repo: `[CI/CD](ci-cd.md)` not the full GitHub URL.
- Link the first mention of a proper noun (a tool, standard, or file), not every mention.
- Do not link bare words like "here" or "this". Link the noun the reader is navigating to.

## Tables

- Left-align text columns, right-align numeric columns.
- Single header row.
- Empty cells show `-`, not blank.
- Do not use HTML inside Markdown tables unless alignment or span is required.

## Code in prose

- File paths, function names, and env var names in backticks: `scripts/sync_from_registry.py`, `render_template()`, `GITHUB_TOKEN`.
- Shell command examples always prefixed by the command itself, never a `$` or `>` prompt.
- Long output is elided with `# ... truncated ...`, not real output dumps.

## Review checklist

Before committing any prose change, verify:

- [ ] No em/en dashes, smart quotes, ellipses, or emoji.
- [ ] H1 title present, followed by an overview paragraph.
- [ ] No marketing language or LLM-tell phrases.
- [ ] All file references are backticked, all cross-doc links are relative.
- [ ] Length budget respected for the document type.
