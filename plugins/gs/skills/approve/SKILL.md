---
name: approve
description: "Accept what Claude showed you. Type this when Claude asks for your decision on the spec, the plan, a part of the build, or the final result. The project then records your approval and the next step can start. You can add a note, for example: /gs:approve but keep the summary short."
argument-hint: "[optional note]"
disable-model-invocation: true
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Approve

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - To approve is to accept what Claude showed. The approval goes on the record of the project.
  - The spec is the written agreement of what the result must do. The plan is the order of the work, in phases. A phase is one small part of the plan.

## Rules that matter

- The approval is the person's. This skill runs only because they typed `/gs:approve`; a "yes" or "looks good" in the chat is not an approval, and you never approve for them.
- A refused approval means something real is not ready. Do not retry it another way.
- Do not tidy an approved `SPEC.md` or `PLAN.md` afterwards: any change to an approved file needs a new approval.

## Steps

1. Look for the gs note that came with this turn. When the plugin's automatic reminders are on, they record the approval the moment it is typed.
   - The note says the approval "is now recorded": run nothing and go to step 4.
   - The note says it "could not be recorded", with a reason: go to step 3.
   - No such note: go to step 2.

2. Run `GS status`. If nothing is waiting, say so in one sentence and end on the `NEXT:` line. Otherwise run `GS approve --note "<the words typed after /gs:approve>"`, or plain `GS approve`.

3. If it was refused, say why in one sentence and name the one thing to do:
   - the spec or plan has a gap the format check found: `/gs:2-define` for the spec, `/gs:3-design` for the plan;
   - the check is failing: `/gs:fix`;
   - the verdict is NOT PROVEN: say what is unproven and offer `/gs:fix`;
   - anything else: the line it printed, in plain words, then `/gs:help`.

4. Tell the person in one sentence what is now on record, for example "The project now records your approval of the spec. The Design step can start." End on the `NEXT:` line, as "Next, type `/gs:<step>`.", with one sentence that says what that step does.
