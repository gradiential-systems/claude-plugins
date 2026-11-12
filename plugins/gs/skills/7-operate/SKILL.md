---
name: 7-operate
description: "Step 7 of 7. Keep it working. Claude tells you if the latest runs were normal. If you want a change, Claude writes it down as a change request. You can also ask Claude to give the work to a colleague. Use when the person asks \"did it run today\", \"is it still working\", \"today's result looks off\", \"I want it to also do X\", \"hand this over\" or \"I keep doing this by hand\"."
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Step 7 of 7: Operate

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

Done means: the person knows in five sentences whether the last run happened and was normal, and any problem or wish is on its way through the right command.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - A run is one use of the finished result. The run log is the list of runs and what each run did.
  - The check is a set of automatic tests. It gives one result: pass or fail.
  - A change request is a short file that describes one change the person wants.

## Rules that matter

- Read the run log and the newest output before judging. A run that did not happen and a run that found nothing look alike in a summary.
- Report in at most five sentences.
- Something wrong goes to `/gs:fix`. A new wish is a change request that goes through `/gs:2-define`, not a quick edit, because the spec stays the agreement every later step checks against.

## Steps

1. Run `GS status` and act on it. `docs/run-book.md` says where the run log and outputs are; without a run-book the next command is `/gs:6-deploy`.

2. Read the last several entries of the run log and the newest output. Work out the usual range of each count from the earlier runs, so "unusual" means unusual for this project.

3. Run `GS check`. A passing check with a strange real output points at the data or a connection; a failing check points at the scripts.

4. Report in one short paragraph, in this order: whether the run happened and when; anything unusual, with the usual range; the counts; the check result; the one next step. For example: "The last real run was today at 07:46. One thing is unusual: the orders file had 0 rows, and the last six runs had 40 to 90 rows. The run read 3 sources. The check passed on test data, so the scripts are correct. Next, type `/gs:fix`. We then find why the orders file was empty." If nothing is unusual, say so in one sentence.

5. Route what you found, recommending one step:
   - Something wrong: `/gs:fix`. If the cause is a sign-in to a connected service that has gone stale, say so: the person signs in again and reruns the command; that is not a defect.
   - A wish for something new or different: run `GS change new "<title>"` with a title in the person's words, fill the new file's `## What should change` (what happens now, what they want instead) and `## Why`, and give `/gs:2-define` as the next command, naming the change file.

6. After an incident (a missed run, a wrong output, a fix), offer to turn it into a lesson; on a yes run `GS guide lessons` and follow it.

7. If the person asks to hand the work to a colleague or to carry on in a fresh session, run `GS guide handoff` and follow it. If they describe something they keep doing by hand, run `GS guide make-skill` and follow it.

8. End on one next command: `/gs:fix`, `/gs:2-define`, or, if everything is normal, "After the next run, type `/gs:7-operate` again."
