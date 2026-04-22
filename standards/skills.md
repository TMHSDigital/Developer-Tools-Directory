# Skills

A skill is a Markdown file under `skills/<skill-name>/SKILL.md` that gives an AI agent focused instructions for a specific task or domain. This standard defines the required structure, frontmatter, and writing conventions.

## Folder layout

```
tool-repo/
  skills/
    <skill-slug>/
      SKILL.md            # required
      reference.md        # optional, linked from SKILL.md
      examples/           # optional
```

The skill slug is kebab-case. It matches the `name` field in frontmatter (with dashes for spaces) and appears in `plugin.json` under the `skills` array.

## Required frontmatter

Every `SKILL.md` opens with a YAML frontmatter block:

```yaml
---
name: skill-slug
description: One-line summary of what the skill does and when to use it.
triggers:
  - "natural-language trigger phrase"
  - "another trigger phrase"
---
```

Required fields:

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Kebab-case, matches folder name |
| `description` | string | Under 200 characters, starts with a verb |
| `triggers` | string[] | 3-8 natural-language phrases that should invoke the skill |

Optional fields:

| Field | Type | Notes |
| --- | --- | --- |
| `scope` | string | Glob pattern restricting when the skill applies |
| `when_to_use` | string | Longer guidance for agent routing |
| `model_hint` | string | Suggested model family if relevant |

## Body structure

```markdown
# <Skill Title>

<One-paragraph overview of what this skill does and when it is appropriate.>

## When to use

- Bulleted list of trigger scenarios with concrete signals.

## When NOT to use

- Scenarios where a different skill or direct tool call is better.

## Steps

1. Numbered, imperative steps.
2. Each step is a single action.

## Examples

<Short example of good invocation. Include expected outputs where useful.>
```

Sections beyond these are allowed when they add value: `Common pitfalls`, `Reference`, `See also`. Do not pad with filler sections.

## Trigger phrases

- Each trigger is a phrase a user or agent might actually type or think.
- Include the action and the noun: "run the linter on staged files", not "linter".
- Avoid single-word triggers.
- Include common misspellings or alternate phrasings only if they are realistic.
- 3 triggers is the floor, 8 is the ceiling.

## Length

Under 250 lines total. If the skill needs more detail, move it into `reference.md` or `examples/` and link from `SKILL.md`. Progressive disclosure is the default pattern: short main file, deeper files linked.

## Content rules

- Follow [writing-style.md](writing-style.md) for punctuation, voice, and no-emoji rules.
- No external HTTP URLs in skill bodies unless documentation is explicitly referenced and pinned by version.
- No credentials, API keys, or production data in examples. Use placeholder values (`your-api-key`, `example.com`).
- Code blocks declare a language.

## Relationship to `plugin.json`

Every skill listed in `.cursor-plugin/plugin.json` `skills` array must point to a real `SKILL.md` file. The `validate.yml` workflow enforces this.

```json
{
  "skills": [
    {
      "name": "scaffold-resource",
      "path": "skills/scaffold-resource/SKILL.md"
    }
  ]
}
```

## Testing

Every skill is covered by one frontmatter-validation test (see [testing.md](testing.md)):

- Frontmatter parses as YAML
- Required fields present
- `name` matches folder name
- At least 3 `triggers`

## Examples from the ecosystem

See existing skills in Docker Developer Tools, Mobile App Developer Tools, and Home Lab Developer Tools for reference implementations. When in doubt, match the shape of a skill from a repo at `active` status.
