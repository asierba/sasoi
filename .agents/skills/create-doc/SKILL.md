---
name: create-doc
description: Create or improve documentation based on the current conversation. Use this when the user states a convention, principle, or decision that should be documented. Also use when a plan or code change was rejected for not following the repository's conventions.
---

Based on the current conversation, create new or improve existing documentation files inside the `docs/` folder.

## Steps

1. Identify conventions, patterns, or decisions discussed in the conversation that should be documented.
2. Check if a relevant doc already exists in `docs/`.
   - If it exists, improve it while preserving the required structure.
   - If it does not exist, create a new file in the appropriate subfolder.
3. Read @.agents/skills/create-doc/documentation-guidelines.md and follow its structure exactly.
4. Ask the user to confirm the target file path before writing.
5. Update the AGENTS.md docs map with the new doc.

## Rules

- Each convention goes in its own standalone Markdown file — never bundle multiple conventions into one doc.
- Include concrete good and bad examples with code blocks when applicable.
- Link to real files in the codebase that follow the convention in the "Real world examples" section.
