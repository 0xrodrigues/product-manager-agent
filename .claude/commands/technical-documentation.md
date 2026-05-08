---
description: Generate and update standardized technical documentation with mandatory metadata (creation date, last update, version). Use when user requests technical documentation, technical explanations, or module/flow behavior analysis.
---

Generate or update a standardized technical document for: $ARGUMENTS

## Rules

1. Save all documents to `docs/memory/technical-documents/` using kebab-case filenames (e.g., `session-manager.md`, `prompt-assembly-flow.md`)
2. Use the template structure defined in `.claude/technical-documentation/DOC_TEMPLATE.md`
3. Always include mandatory metadata:
   - `Creation date`: today's date (YYYY-MM-DD) — keep original if updating
   - `Last update`: today's date
   - `Document version`: start at `1.0.0`; increment following semver on updates:
     - `major`: large structural scope change
     - `minor`: new sections or relevant behavior expansion
     - `patch`: small adjustments, text corrections, or refinements

## Process

1. Identify what needs documentation (file, module, flow, or service)
2. Read the relevant source files thoroughly — understand actual behavior, not desired behavior
3. Map components, inputs, outputs, and error cases
4. Check if a doc already exists in `docs/memory/technical-documents/` — if yes, treat as update with version bump
5. Fill the template with real behavior only (no speculation)
6. Validate that all code references, endpoints, and models mentioned are accurate
7. Write the final document to `docs/memory/technical-documents/<subject-name>.md`

## Key Constraints

- **Location:** `docs/memory/technical-documents/` only
- **Template:** Always follow `.claude/technical-documentation/DOC_TEMPLATE.md` structure
- **Metadata:** Never omit creation date, last update, or version
- **Accuracy:** Document actual behavior observed in code — not intended or speculative behavior
- **Scope:** One focused topic per file
