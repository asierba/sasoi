# Documentation guidelines

## Structure

Each documentation file follows this template:

```markdown
# [Category]: [Title]

## Convention

[Convention summary - 1-2 sentences explaining the rule.]

## Benefits

- [Benefit 1.]
- [Benefit 2.]

## Examples

### Good: [Brief description of the good practice]

[Code block or description.]

### Bad: [Brief description of the bad practice]

[Code block or description.]

## Real world examples

- [`Component/File Name`](./path/to/file.py)

## Exceptional cases: When to not take into account this convention

[List of cases where exceptions are valid.]

## Related agreements

- [Related agreement title](./path-to-related-agreement.md).
```

## Title and file name

The filename is critical: AI agents use it to decide whether to load the document or not. A descriptive filename ensures the convention is discovered and applied; a vague one means it will be ignored.

Use kebab-case for the filename, derived from the title. Reflect in the title and filename the actual convention instead of the generic category or concept.

Examples:

- "Dependency direction in hexagonal architecture" → `dependency-direction-in-hexagonal-architecture.md`.
- "Factory methods for test fixtures" → `factory-methods-for-test-fixtures.md`.
- "Ports depend on interfaces only" → `ports-depend-on-interfaces-only.md`.

## Good and bad examples

- Use the appropriate code language in fenced code blocks.
- Avoid code comments in the example snippets. Provide a brief description between the heading and the code block only if really necessary.
- Keep examples as brief as possible.

## Optional sections

- If the convention doesn't have exceptional cases, omit the "Exceptional cases" section entirely.
- If there are no real world examples, omit the "Real world examples" section entirely.
- If there are no related agreements, omit the "Related agreements" section entirely.

## Style

- Maximize information density: convey as much as possible in as few words as possible.
- End each phrase with a period, including bullet point items.
