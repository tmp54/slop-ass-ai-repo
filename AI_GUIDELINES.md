## 1. AI Tools and Boundaries

We may use AI tools such as ChatGPT, GitHub Copilot, or similar assistants for brainstorming, explaining concepts, debugging, code suggestions, documentation, and test generation.

AI-generated output must not be accepted blindly. Any code, design, or technical claim produced by AI must be reviewed and understood by a team member before being included in the project. Security-sensitive or critical logic requires additional human review.

## 2. Documentation Rules

AI usage should be documented when it meaningfully contributes to the project.

* Prompt Engineering Log: record important AI interactions whose output is used in the project.
* `DECISIONS.md`: record cases where AI contributes to a significant design or architectural decision, including the team’s reasoning.
* Pull Request description: disclose when AI-generated or AI-assisted code is included in the PR.
* Trivial uses, such as syntax explanations or minor debugging help, do not need to be recorded.

## 3. Resolving Disagreements

AI output is treated as a suggestion rather than authoritative evidence.

When team members disagree about AI-generated output, we evaluate it using tests, documentation, specifications, experiments, or other reliable sources. Code must pass relevant tests and review before being merged.

If disagreement remains after reviewing the evidence, the team member responsible for that component makes the final decision, and significant decisions are recorded in `DECISIONS.md`.

