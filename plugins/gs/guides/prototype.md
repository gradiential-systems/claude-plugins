# Prototype

Done means: the person has answered the one question by looking at something real, the answer is in `docs/decisions.md`, and the person has heard that the prototype is not the product.

## Rules that matter

- One question per prototype, written at the top of the file, because a prototype that tries to answer several questions answers none of them clearly.
- Write only inside `prototype/`. Code there does not wait for an approved spec and plan, and that is safe only while the prototype stays throwaway: nothing outside the folder may use it, and nothing in it is copied into the product. What the answer settles is built again through the normal flow.
- Make something a non-programmer can open: one HTML file that opens by double-click (no server, no internet, everything in the one file), or one sample output file. Use the person's own words for every label and heading, from the conversation and `GLOSSARY.md`, because they are judging their domain, not reading code names.
- Show the whole result after every click or choice, so the person can see exactly what changed.

## Steps

1. Run `GS status` and act on it.
2. Settle the question in one sentence and pick the shape:
   - "What should it look like?": one sample output, or two or three clearly different versions side by side in one HTML file, each labelled.
   - "Would this rule feel right?": one HTML file with a button per case (for example "an order with no date", "a customer listed twice") that shows what the rule does with it, including the awkward cases that are hard to picture on paper.
   If the shape is unclear, ask one question with the recommended shape first.
3. Use invented examples or the project's test data, unless the person asks to see their own data, because invented cases make the edge cases easy to show.
4. Write `prototype/<slug>.html` or `prototype/<slug>-sample.<ext>`. First line, visible on the page: "Prototype, not the product. Question: <the question>."
5. Tell the person where it is and how to open it (double-click the file in the project's `prototype` folder), then ask the one question, with options written in the chat and your recommendation first.
6. Record the answer as one line in `docs/decisions.md` (create it with the heading `# Decisions` if missing), numbered after the last line: `D<n>. <the answer, in the person's words> (asked, seen in prototype/<file>): <what it changes in SPEC.md or docs/design.md>`.
7. Say plainly: "The prototype is not the product. The answer goes into the spec or the design, and the real thing is built from there." If SPEC.md or `docs/design.md` was already approved, say that adding the answer reopens that gate.
8. End on one exact next command: `/gs:2-define` if the answer changes what it must do, `/gs:3-design` if it changes how it is built, otherwise the `NEXT:` line of `GS status`.
