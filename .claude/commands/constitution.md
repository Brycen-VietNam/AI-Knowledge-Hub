# /kh.constitution

Establish or review project constitution — core principles, hard constraints, non-negotiables.
Run ONCE at project start. Review when architecture changes significantly.

## Usage
```
/kh.constitution [create|review|update]
```

## Execution Flow
```
create:  check if CONSTITUTION.md exists → if yes, warn + ask confirm
         copy .claude/templates/constitution/_template.constitution.md
         fill from CLAUDE.md tech stack + team input
         save to CONSTITUTION.md (project root)

review:  load CONSTITUTION.md + last 3 spec files
         flag any specs that violate principles
         output violation report

update:  show current principles as numbered list
         accept change as: "update P003: <new text>"
         never rewrite wholesale — only targeted updates
         git diff style output
```

## Output (create mode)
```markdown
## CONSTITUTION.md created
Principles: N
Constraints: N
Non-negotiables: N

Review and commit before starting /specify work.
Violations found in existing specs: [none | list]
```

## Agent Instructions
- Model: **sonnet** (claude-sonnet-4-6)
- Token budget: 2k tokens
- Load CLAUDE.md only (not full codebase)
- If CONSTITUTION.md already exists → diff against it, do not overwrite
- Every /checklist and /rules auto-references this file
- Token budget: 2k tokens max
