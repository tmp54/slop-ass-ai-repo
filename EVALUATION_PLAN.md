# Evaluation Plan

## Problem Grounding

1. Who specifically has the collaboration problem you are addressing?
   Members of 3–5 person student software teams (and lab teams) when half-finished work passes from one person (sender) to another (receiver). Evidence from outside users: see `CP1.md` section 2 **[add the interview summaries here too]**.
2. What do they currently do instead of your tool?
   A chat message, an issue, or a call; sometimes an issue template or checklist. Our baseline for testing is a GitHub issue template with required fields plus a convention that the receiver comments a restatement and the sender reacts to confirm.
3. What would be observably different about their collaboration if your tool worked?
   The receiver can correctly state the next steps right after the handoff and asks the sender noticeably fewer clarifying questions.

## Evaluation Plan Draft

- **Success definition:** In a simulated handoff, receivers using the tool score at least 1 more key fact (out of 5) than with the baseline on average, and ask at least 30% fewer clarifying questions in the 15 minutes afterwards.
- **Target users:** Pairs of students who already work together, from other groups in this course and from labs or other courses we can reach. Not on our team. Recruited by a sign-up sheet in class and on the course channel (Week 10), plus our own contacts.
- **Method:** Structured observation. Each pair does one handoff with the baseline and one with the tool (order alternated), observed by a team member with a pre-written 5-fact answer key. Pilot with 2–3 pairs in Weeks 10–11, main evaluation with at least 6 pairs in Weeks 13–14.
- **Minimum evidence threshold:** At least 6 pairs (12 people); higher restatement score with the tool for at least 5 of 6 pairs; at least 30% fewer clarifying questions on average; at least 4 of 6 receivers prefer the tool for a real handoff. Reported as directional evidence. If the baseline does as well, we report that.
- **Human-AI boundary:** AI organises notes and flags gaps; humans decide what is true, why decisions were made, whether to send, and whether the receiver understood. Whether to include AI is decided by Week 9 and tested in the pilot against a blank template.
