# Research

Done means: `docs/research/<slug>.md` exists, every claim in it names its source, and the person has the answer in two sentences.

## Rules that matter

- Never state a looked-up fact without its source, in the note or in chat, because an unsourced fact in a spec becomes an assumption nobody checks.
- Primary sources first: the vendor's own documentation and help pages, the official specification, the actual file or data in the project. Use a secondary write-up only when nothing primary exists, and say so, because write-ups go out of date and copy each other's mistakes.
- A fact, not a decision. If the question is really "what should we do", find the facts, then put the decision to the person as one question with a recommended answer.

## Steps

1. Run `GS status` and act on it.
2. Restate the question in one sentence. If it has two readings, ask one question to choose, recommending the likelier one.
3. Look it up. For a connected service, the primary source is the provider's own reference documentation. If the search will take more than a few minutes, run it as a background agent so the person can keep working, and say so.
4. Write `docs/research/<slug>.md`, where the slug is a few words of the question joined by hyphens:
   ```
   # <the question>

   ## Answer
   <two sentences>

   ## Sources
   - <title>, <link>, read <date>: <what it says, quoted where short>

   ## Confidence
   High, medium or low, and why in one sentence.

   ## Not checked
   <what was not looked at, or could not be confirmed>
   ```
5. Report the answer in two sentences, with the note's path. If the answer changes something in SPEC.md or `docs/design.md`, say which line, and that changing an approved file reopens its gate (the person approves it again).
6. End on one exact next command: the step that was underway, from the `NEXT:` line of `GS status`, or `/gs:2-define` or `/gs:3-design` if the answer changes the spec or the design.
