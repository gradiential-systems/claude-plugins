# Gradiential plugins for Claude Code

This repository is the Claude Code plugin marketplace of Gradiential Systems. Its name is `gradiential`.

## Plugins

- **gs**: a guided way for people who are not programmers to build small tools with Claude Code. You decide what Claude builds, and you check the result. See [`plugins/gs/README.md`](plugins/gs/README.md).

## Install

Open the Claude desktop app. Open the Code tab in a local session. Type these two lines into the prompt box, one at a time:

```
/plugin marketplace add gradiential-systems/claude-plugins
/plugin install gs@gradiential
```

Then start a new session and type `/gs:help`.

## For maintainers

- Each plugin is a folder under `plugins/`, with its own `.claude-plugin/plugin.json`, README and tests.
- `.claude-plugin/marketplace.json` lists the plugins. A plugin has no `version` field, so each commit is a new version.
- Test a plugin before a push: `python3 -m unittest discover -s plugins/gs/tests` and `claude plugin validate plugins/gs`.

## Licence

MIT. See `LICENSE`. Each plugin credits its sources in its own `NOTICE.md`.
