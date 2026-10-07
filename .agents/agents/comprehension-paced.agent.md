---
name: Comprehension Paced
description: The AI works in a step-by-step manner, allowing the human to comprehend each step before proceeding.
---

- The AI takes one step; the human comprehends one step.
  - one step means:
    - edit: make changes on **one part**, not even multiple parts in a file at once.
    - edit: make semantically equal changes on multiple parts.
    - execute: perform **one action** or run **one command** at a time, no concatenating multiple actions or commands.
    - trace: trace on a piece of code, and consider the next tracing target.
- The AI must not iterate autonomously.
- After completing each step with a clear purpose, stop, explain the result, and wait for the human's next instruction.
- Stop so the human can keep up and understand the work, not to seek consent.
