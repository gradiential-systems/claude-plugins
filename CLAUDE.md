# Gradiential plugins

The public Claude Code plugin marketplace of Gradiential Systems (`gradiential`), published at `gradiential-systems/claude-plugins` on GitHub. Each plugin is a folder under `plugins/`.

- This repository is public. Nothing client-specific, and no person's data, goes into it.
- A plugin's own text names no connector, no particular project and no client. A ready-made project (a starter) ships as its own plugin, never inside `gs`.
- Text that a plugin gives its user follows the writing rules in `plugins/gs/skills/*/SKILL.md` ("How to write to the person").
- Test before a commit: `GS_PYTHON=<python 3.11+> python3 -m unittest discover -s plugins/gs/tests`, then `claude plugin validate plugins/gs` and `claude plugin validate .`.
- Push only when Na'im asks. Every push is a release, because plugins carry no version field.
