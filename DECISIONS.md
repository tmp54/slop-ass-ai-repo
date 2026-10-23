# Decisions Log

## 2026-09-21 — Initial code steward
**What:** tmp54 is the initial code steward for the team.
**Why:** try try see

## 2026-10-23 — Build a handoff tool for student software teams
**What:** We will build a tool that turns a sender's rough notes into a structured handoff brief and confirms that the receiver understood it (receiver restates the next steps, sender checks) before a handoff counts as done.
**Why:** When work changes hands, the receiver cannot tell from issues or commits what is done, which decisions are final, or what traps exist, and nobody checks that the receiver understood. Existing tools (Jira required fields, Asana approvals, GitHub issue forms, Notion/Trello checklists) store a handoff or enforce structure, but none makes the receiver show understanding.
**Alternative rejected:** Meeting action-item extraction (crowded: Fireflies, Fathom, Otter already do it); PR rationale capture (the course's own example, so hard to stand out and already partly covered by PR templates); peer contribution tracking (CATME exists and research evidence is mixed).
**Led by:** [name]
**Status:** Provisional until the two outside-user conversations (CP1) confirm the problem is real. If they do not, we revisit this decision and record the change here.

## 2026-10-23 — Evaluation baseline is a GitHub issue template plus comment convention
**What:** We will compare our tool against a baseline of a GitHub issue template with required fields, plus a convention that the receiver comments with a restatement and the sender reacts to confirm.
**Why:** The baseline costs almost nothing and students already use GitHub, so it is the realistic alternative. If our tool cannot beat it, we should not claim it helps.
**Alternative rejected:** Comparing against "no structure at all". That would be an easy win but would not convince a skeptic.
**Led by:** [name]

## 2026-10-23 — AI in the tool is provisional and must be justified by Week 9
**What:** The AI may organise the sender's notes into sections and flag gaps between the notes and the diff. It does not write rationale and nothing is sent without the sender's approval. We decide by Week 9 whether to include AI at all, and test it in the Week 10–11 pilot against a blank template.
**Why:** The course grades whether AI use is justified. The main risk is a brief that looks complete but is wrong, so every item is tagged with its source (sender said / seen in diff / AI inferred).
**Alternative rejected:** Letting the AI write the full brief and rationale automatically (it would invent reasons and remove the sender's responsibility for accuracy).
**Led by:** [name]
