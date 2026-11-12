---
name: 2-define
description: "Step 2 of 7. Agree what to build. Claude asks you a few questions, one at a time. Then Claude writes the spec, which is the short written agreement of what the result must do. You approve it. Use when the person says \"write the spec\", \"let's define it\", \"what exactly should it do\", \"interview me about what I want\", or the next step is /gs:2-define."
allowed-tools: Bash(python *gs.py*), Bash(python3 *gs.py*), Bash(py *gs.py*), PowerShell(python *gs.py*), PowerShell(py *gs.py*)
---

# Step 2 of 7: Define

`GS` means `python "${CLAUDE_PLUGIN_ROOT}/scripts/gs.py"` (`python3` on macOS). Run each `GS` command by itself, never joined with `;` or `&&`: only the plain command runs without a permission prompt. You run commands; the person types only `/gs:` commands and never opens a terminal.

## How to write to the person

The person is an expert in their own work and is not a programmer. Everything they read must obey these rules: your messages in the chat, and the files you write for them.

- Write full sentences in short paragraphs. Use a numbered list only for choices, steps and items to check.
- Use at most 20 words for an instruction and 25 words for a description. Put one idea in each sentence.
- Use the active voice and say who does what. Put a condition before its instruction: "If the check fails, type `/gs:fix`."
- Use one word for one thing, and the same word every time.
- Use plain words. Do not use abbreviations, idioms, contractions or symbols in place of words. Use the person's own name for a thing, not its file name, unless they must open the file.
- Explain a technical word in one sentence the first time you use it in the conversation. Use these meanings:
  - The spec is the short written agreement of what the result must do. Its file is `SPEC.md`.
  - An acceptance check is one line of the spec. It says what must be true and how we test it.
  - To approve is to accept what Claude showed. Only the person approves, and they do it when they type `/gs:approve`.

## Rules that matter

- Facts are your job; decisions are theirs. Never ask what `docs/explore-notes.md`, `docs/starter-brief.md` or a file in the folder already answers.
- Ask at most the question cap (`question_cap` in `.gs/starter.json`, five when it is not set), and only questions whose answers change what gets built, because the person's attention is the scarcest thing here.
- Promise in the spec only what will be built and checked, because Verify tests every acceptance check as written and one unmet promise makes the result NOT PROVEN. State rules and behaviours rather than figures, and write a specific number, total or date into a check only if you computed it with a command in this session.
- Build and design nothing here. A "yes" in the chat accepts a recommended answer; only a typed `/gs:approve` accepts the spec.

## Steps

1. Run `GS status`. If the spec is already approved, say so and end on the `NEXT:` line, unless the person asked to change it (then say that changing it needs a new approval, and go to step 5).

2. Read `docs/explore-notes.md`, and where present `docs/starter-brief.md`, `docs/decisions.md`, a `SPEC.md` the starter brought, `.gs/starter.json`, and the open change file in `docs/changes/` if this is a change to something already built. If `docs/explore-notes.md` is missing, the Explore step comes first: end on `/gs:1-explore`.

3. Pick the questions. From the open questions in the notes, keep those whose answer changes what gets built or what the checks expect, and order them by how much the answer changes. Everything else becomes a stated assumption.

4. Interview, one question per turn. Before the first question, give a two-sentence read-back of what you understand they want, and say "If this is wrong, tell me before you answer.". Each question has:
   - the question as a full sentence in their words, never a section name or a label from a document;
   - one sentence on why it matters;
   - the options as a numbered list in the chat, recommended first and marked "(Recommended)", each with one clause on what it would mean, and also offered through the question tool when it is available;
   - the sentence "If you answer yes, I use the recommended answer."

   If they say "whatever you think", state the recommended answer back and ask them to confirm it. After three accepted recommendations in a row, ask the next question without a recommendation, so the answer is theirs. If an answer contradicts an earlier one, make that the next question.

   As each answer lands, add one line to `docs/decisions.md` (heading `# Decisions`): `D<n>. <the decision> (asked | found in <file> | assumed): <one clause why>`. Assumptions go there too. Re-read this file before asking anything after a break, because it is the record that survives a fresh session.

5. Write `SPEC.md` with exactly these headings, in this order, in plain words:
   - `## Summary`: at most 120 words: what it is, who reads it, what it produces.
   - `## Who it is for`
   - `## Inputs`: each source, what is read, for which period.
   - `## Output`: what the person receives, where, and its parts.
   - `## Acceptance checks`: a numbered list, at most eight. Each names one result that could be wrong and is followed by a line starting "How we check:" that says what is compared with what, because a check is useful only if it could have failed. For example: "3. An order with no delivery date is listed under Needs attention." then "How we check: a test file holding one such order must show it there, and the same order with a date must not." When the project comes from a starter, its tests, template and expected output are fixed: build the checks from the "done when" line of each phase in `.gs/starter.json`, from `docs/starter-brief.md` and from the person's decisions, and add nothing the fixed design cannot satisfy.
   - `## Out of scope`: what this deliberately does not do, including anything the person ruled out.
   - `## Decisions`: the lines from `docs/decisions.md`, including setting values the person chose; the build copies them into the settings file later.
   - `## Open questions`: empty, or each line ending "deferred: <reason>". Questions beyond the cap go here, or under Decisions as assumptions.

6. Run `GS lint spec` and fix each line it prints until it prints none. Then run `GS done define`.

7. Present the decision, and nothing else in that message, in this order:
   - one sentence that says the spec is ready and what a spec is;
   - the Summary as written;
   - the acceptance checks as a numbered list, each a full sentence. If there are more than five, show the five that matter most and say how many more are in the file `SPEC.md`;
   - the choice: "You have three choices. To accept the spec, type `/gs:approve`. To revise it, tell me what to change. To stop, say stop. If you stop, I delete nothing."

8. If they ask for changes, edit `SPEC.md`, record each change in `docs/decisions.md`, and repeat steps 6 and 7. If they stop, record that in `docs/decisions.md` and say: "To continue later, type `/gs:help`."

## If the person cannot picture the result

Offer a rough version first: run `GS guide prototype` and follow it.
