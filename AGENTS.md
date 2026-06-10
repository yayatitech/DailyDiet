# AGENTS.md

## Project Agent Instructions

This project should be developed with cost-efficient AI usage.

### Default behavior
- Prefer small, targeted changes.
- Do not perform broad repository analysis unless asked.
- Use existing patterns before creating new abstractions.
- Keep responses concise.
- Avoid unnecessary dependency additions.

### Documentation first
Before large features, update or consult
- `docsarchitecture.md`
- `docsfeatures.md`
- `docsdecisions`
- `docstesting.md`

### Validation
Prefer the smallest useful validation command
- Single unit test
- Single package test
- Typecheck for affected package
- Lint only affected files when possible

### Safety
Ask before
- Database migrations
- Deleting files
- Resetting git state
- Installing dependencies
- Running expensive full test suites
- Changing authentication, billing, permissions, or production config