---
name: Additive API fields — consumer contract over runtime check
description: When consumers are not yet built, enforce JSON parsing rules in the rendering contract (docs) rather than treating it as a blocker or adding feature flags
type: feedback
---

When a new additive field is added to an API response and consumers don't yet exist, do NOT treat strict-parsing risk as a blocker or propose a feature flag.

**Why:** Consumers not yet implemented means risk is zero at the time of API change. A feature flag adds implementation cost and complexity for a problem that doesn't exist yet. The correct action is to encode the constraint in the consumer-facing contract (e.g., rendering contract doc, AC, or API reference) so future consumer developers inherit the rule by default.

**How to apply:** When clarifying API-additive changes (Option C pattern), check if consumers exist first. If not: resolve the question as N/A, add an explicit AC to S004 (or equivalent contract story) mandating permissive JSON deserialization, and move on. Only escalate to feature flag if at least one consumer is already in production with strict parsing confirmed.
