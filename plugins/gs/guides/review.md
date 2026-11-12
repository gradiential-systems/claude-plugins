# Review

Done means: the person has both verdicts side by side, at most five findings each, and one decision to make.

## Rules that matter

- Two reviewers, kept apart, each given file paths only. A reviewer who sees the other's findings, or the builder's account of what it did, tends to agree instead of looking.
- Report the two side by side, never merged or re-ranked, because a result can pass one question and fail the other, and merging lets one hide the other.
- At most five findings each, most serious first, then one decision, because the person's attention goes to the first few lines.
- Say plainly: two AI reviewers agreeing is weaker evidence than the person's own hands-on check. Both are the same kind of model reading the same files, so they tend to miss the same things.

## Steps

1. Run `GS status` and act on it. A review needs an approved SPEC.md and some built work; if either is missing, give the command status names instead.

2. Collect paths, not contents:
   - For the spec reviewer: `SPEC.md`, `GLOSSARY.md` if present, the code and test folders, the newest outputs, and the newest check log in `.gs/logs/`.
   - For the standards reviewer: `docs/design.md`, the project's CLAUDE.md, the code and test folders, the template and rules files, and the newest check log.
   - Leave out `docs/verify-report.md`, `HANDOFF.md` and any summary of what Claude says it did, because the reviewers judge the files, not the claims.

3. In one message, start both reviewers with the Agent tool so they run in parallel: subagent type `gs:spec-reviewer` and subagent type `gs:standards-reviewer`. Each brief is one sentence ("Judge whether this work does what SPEC.md says" or "Judge whether this work is built soundly") plus its list of paths. Nothing else, so neither is steered. Wait for both reports before going on, and do not end the turn while either is still running, because a review reported half-finished gives the person nothing to decide on.

4. Check each finding before it reaches the person: the quoted line or value must exist in the file named (search for it). Drop any finding whose quote is missing, and say how many were dropped.

5. Report in this shape:
   ```
   Against the spec: <n> of <m> acceptance checks met.
   1. Not met: <check in the spec's words>. <one sentence, with the quoted evidence>
   ...
   Built soundly: <n> sound, <n> problems, <n> unclear.
   1. Problem: <in plain words>. <one sentence, with the quoted evidence>
   ...
   ```
   Translate file names into the person's words ("the script that reads your orders file"), keeping the quote.

6. Add the sentence about two AI reviewers, and name the one hands-on check that would settle the most serious finding (for example "open the newest output and compare one figure with your own records").

7. Ask for one decision, recommending one: accept as it is, revise (which finding goes to `/gs:fix` first), or stop. A "not met" or a "problem" goes to `/gs:fix`, where it becomes a failing test before the repair.

8. End on one exact next command: `/gs:fix` for the first finding to repair, or the `NEXT:` line of `GS status` if the person accepts.
