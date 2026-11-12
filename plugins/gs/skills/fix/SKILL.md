---
name: fix
description: "Tell Claude that something is wrong. Say what you saw and what you expected. Claude first makes the problem happen again. Then Claude adds an automatic test that finds it, and corrects the cause. Use when the person says \"something is wrong\", \"it gave the wrong number\", \"this item is missing\", \"the check keeps failing\" or \"that's not right\", or when a build step has failed twice on the same problem."
argument-hint: "[what went wrong, in your words]"
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Fix: every defect becomes a test

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

A defect fixed without a test can come back unnoticed. One turned into a test that failed first is caught by the check from then on.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - A defect is a result that is different from what the spec says, or from what the person expects.
  - A test is one automatic comparison of a result with the expected result. The check is the set of all tests.
  - A version is a saved copy of the project files at one moment. The person can go back to it.

## Rules that matter

- Reproduce before you theorise: make the wrong result happen on demand with the exact input first.
- The new test must be seen failing, for this defect, before any script changes. A test that passes before the fix does not test it.
- Never weaken a check to get a pass: no editing the answer key, the check or an existing test, no loosened expected value, no skipped test. New tests go in new files. Never hand-edit a file a script writes.
- If the system does what SPEC.md says and SPEC.md says the wrong thing, the fix is the person's decision, not yours: see "When the cause is in the spec".
- Keep working until the check passes or you are plainly blocked; the evidence is the `GS check` line from this turn.

## Steps

1. Run `GS status` and act on it. If a phase or the result is waiting for the person's decision, run `GS revise` first, so the record shows they asked for a change.

2. Restate the problem in one sentence with the exact values: what they expected, what they got, where they saw it. Example: "The March summary shows 11 orders for Acme; you expected 12, because the order placed on 31 March at 23:40 is missing." Carry on without waiting, unless the report could mean two different things; then ask which.

3. Reproduce it: run the script or the full run on the same data and date and show the wrong value next to the expected one. If it does not reproduce, say so and ask for one more detail (which date, which item). If the output was right and the expectation was not, show the evidence and stop; that is a valid result.

4. Write a new test in a new file named after the defect (for example `tests/test_defect_late_order_missing.py`). Its expected value comes from the person's records or the spec, never from the code. If it needs a small copy of the person's data with one value changed, keep it in a folder the project leaves out of saved versions (the project's CLAUDE.md names one if it has one), because that data stays on this computer.

5. Run `GS check`. Show the new test failing, naming the expected and the actual value.

6. Find the cause. If it is not obvious, show at most three ranked guesses in plain words, each with what would prove it ("If the order is dropped because its time falls on the next day in another time zone, moving it to midday in the test makes it appear"). Test the top guess with the smallest change without waiting for a reply, and take into account anything the person says.

7. Make the smallest change that fixes the cause.

8. Run `GS check` until it passes, including the new test. Then run the original failing case on the real input and show the corrected value.

9. Add one line to `docs/lessons.md`: date, what went wrong, the cause, the new test's file name.

10. Run `GS save "fix: <what was wrong>"`. To the person, say "I saved a version of the project." Do not name git.

## When the cause is in the spec

Run `GS change new "<short title>"` and fill in the file: what the spec says now, what the person needs instead, and the example that showed it. Leave the failing test in place. Tell the person in two sentences and end on `/gs:2-define`.

## When it will not yield

If three guesses are all wrong, stop changing code. Report what was tried, what each attempt showed, and what you need, for example a second example of the problem.

## Report

One short paragraph: what was wrong, what caused it, and what you changed. Then one sentence with the check result exactly as printed, and one sentence that says the new test now finds this defect each time. End on the `NEXT:` line of `GS status`.
