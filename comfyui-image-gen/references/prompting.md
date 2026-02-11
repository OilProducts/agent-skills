# Prompt Pattern

Use a compact structured spec when preparing text inputs for workflow bindings:

```text
Use case: <illustration-story|product-mockup|photorealistic-natural|stylized-concept|...>
Primary request: <scene goal>
Subject: <who/what is in frame>
Style/medium: <visual style>
Composition/framing: <camera + layout>
Lighting/mood: <time + emotion>
Constraints: <must-keep invariants>
Avoid: <must-not-generate items>
```

Guidelines:
- Be explicit about `no text`, watermark exclusion, and continuity constraints.
- Prefer one controlled change per iteration.
- Keep prompts concise and compatible with your workflow's text encoder limits.
