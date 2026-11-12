---
name: 5-verify
description: "Step 5 of 7. Prove that it works. Claude runs all the automatic tests. A second, independent copy of Claude examines the result. You compare one item with your own records. A script then gives the verdict: PROVEN, PARTLY PROVEN or NOT PROVEN. Use when the person asks \"is it right\", \"does it work\", \"can I trust it\" or \"check it before I use it\"."
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Step 5 of 7: Verify

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

The builder is the worst judge of its own work, so the evidence comes from three places that do not depend on your word: the check, a fresh checker that never sees the build story, and the person's own records.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - The check is a set of automatic tests. It gives one result: pass or fail.
  - The independent checker is a second copy of Claude. It sees only the files, not how Claude built them.
  - A spot check is one item that the person compares with their own records.
  - The verdict is one of three results: PROVEN, PARTLY PROVEN or NOT PROVEN. A script calculates it from the evidence.

## Rules that matter

- "Not checked" is an honest answer; a guess is not. Mark an acceptance check "met" only when this session produced its evidence.
- A missing count is not zero: an empty input and "nothing happened" look the same in the output, so say which it was.
- The verdict is the word `GS verdict` prints, reported exactly. Do not soften it or argue the person into accepting.
- A failure here is a finding, not something to repair in this step. The person decides what happens next.

## Steps

1. Run `GS status` and act on it. If phases remain unbuilt or one is waiting for a decision, give that command instead (`/gs:4-implement` or `/gs:approve`). If the result is waiting for a decision and the person asked for a change, run `GS revise` first.

2. Run `GS check` and quote its summary line. If it fails, stop: say in two sentences what failed and end on `/gs:fix`.

3. If `GS status` shows no canary proof, run `GS canary`.

4. Run the build once on the person's real inputs if that has not happened since the last code change.

5. Start the `gs:checker` subagent with file paths only: `SPEC.md`, the output files, and the input files they were built from (`## The picture` in `docs/design.md` names them). Give it no plan, history, summary or claim that the build passed, because a checker told what to expect tends to find it. Wait for its report before going on.

6. Ask the person for one hands-on spot check against their own records. Pick the one item most likely to be wrong (a count near a boundary, a date near midnight, the first ranked item) and say exactly what to look at, in one question. For example: "Please look in your own order list. How many orders have the date 3 March? The summary says 12." End the turn there. When they answer, continue; if they cannot check now, record "not done".

7. Write `docs/verify-report.md` in this shape:
   ```
   # Verify report
   ## Acceptance checks
   1. [met] <the acceptance check, in the spec's words>. Evidence: <file and the quoted line or value, or the command and its printed result>
   2. [not met] <...>. Evidence: <...>
   3. [not checked] <...>. Reason: <why there is no evidence>
   ## Spot check
   Item: <what the person looked at>
   Result: matched | did not match | not done. <the person's answer in their words>
   ## Check and canary
   <the GS check summary line; the canary result>
   ## Independent checker
   <its per-check results and its top problems, unedited>
   ```
   One line per acceptance check in SPEC.md, same numbers, none skipped, each starting with exactly one of the three marks, because `GS verdict` counts them. Where you and the checker disagree, write "not checked" and quote both.

8. Run `GS verdict`, then `GS done verify`.

## The decision (PROVEN or PARTLY PROVEN)

Write this message and nothing more, in at most 180 words:

1. The verdict word exactly as printed, one sentence that says what that word means, and the one reason that matters most.
2. The evidence as one short paragraph of full sentences: the check result, quoted; that the check failed when you broke something on purpose; how many acceptance checks the independent checker found met, not met and not decided; the result of the spot check; and each acceptance check that nobody checked.
3. The choice: "You have three choices. To accept the result, type `/gs:approve`. To revise it, tell me what to change. If something is wrong, type `/gs:fix` and tell me what you saw. To stop, say stop. If you stop, I delete nothing."

## When the verdict is NOT PROVEN

There is nothing to accept yet. Give the verdict word and say what it means. Then, for each acceptance check that is not met, say in one or two sentences which side is wrong, with the evidence:

- The output is wrong: the next step is `/gs:fix`, one defect at a time.
- The spec is wrong (the output is right, and the spec states a wrong figure or promises something never meant to be built): say so and offer to correct that line of SPEC.md. On a yes, edit the line, run `GS done define`, and ask them to type `/gs:approve`. Never change the spec to pass a check when the output is what is wrong.

After the fix or the correction, run this step again from the top.

## A deeper review

If the person asks for one (two independent reviewers, one against the spec and one against sound-building rules), run `GS guide review` and follow it.
