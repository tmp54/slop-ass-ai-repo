# AI Guidelines

## AI Tools and Boundaries

We will use Claude to draft the first pass of docstrings and API documentation — a human always reviews and edits before it's merged

## Documentation Rules

AI usage should be documented when it meaningfully contributes to the project.

* Prompt Engineering Log: record important AI interactions whose output is used in the project.
* `DECISIONS.md`: record cases where AI contributes to a significant design or architectural decision, including the team’s reasoning.
* Pull Request description: disclose when AI-generated or AI-assisted code is included in the PR.
* Trivial uses, such as syntax explanations or minor debugging help, do not need to be recorded.

## Resolving Disagreements

AI output is treated as a suggestion rather than authoritative evidence.

When team members disagree about AI-generated output, we evaluate it using tests, documentation, specifications, experiments, or other reliable sources. Code must pass relevant tests and review before being merged.

If disagreement remains after reviewing the code steward makes the final decision, and significant decisions are recorded in `DECISIONS.md`.
