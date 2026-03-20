# Prompt Caching Strategy (Anthropic-first)

## Prompt Cache Policy v1 (document interface)
- `stable_prefix_rules`
- `dynamic_suffix_rules`
- `api_cache_control_policy` (optional, only for direct Anthropic API path)

## Route A (default): Stable Prefix
Use for all Claude Code slash-command and subagent handoff flows.
- Keep prefix fixed across calls: role/system, invariant rules, fixed file-load order, output contract.
- Put only volatile data in suffix: task id, fresh diff, blocker, user input.
- Reuse the same block order for higher cache hit and lower prompt cost.

## Route B (optional): Explicit `cache_control`
Use only when integrating direct Anthropic API calls outside normal slash-command flow.
- Apply `cache_control` to stable prompt blocks only.
- Keep Route A structure (stable prefix + dynamic suffix) even when `cache_control` is used.
- Not required for default Claude Code slash-command operation.

## Cache-breakers to avoid
- Changing stable block order between similar requests.
- Injecting timestamp/random/session-id into prefix.
- Inserting dynamic files/content at the beginning of prompt.

## Prompt frame (short template)
```text
Stable Prefix:
1) Role + invariant constraints
2) Fixed rule bundle order
3) Fixed file/context load order
4) Expected output contract

Dynamic Suffix:
- task_id / feature
- latest diff or runtime signal
- blocker / user-specific request

Expected Output:
- 3-line summary
- status + next action
```

