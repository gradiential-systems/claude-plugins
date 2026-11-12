"""Tests for scripts/gs.py. Run from the plugin root: python3 -m unittest discover -s tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

GS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "gs.py")

SPEC = """# Spec

## Summary
A small tool that adds two numbers and prints the total.

## Who it is for
Me.

## Inputs
Two numbers.

## Output
One number.

## Acceptance checks
1. Adding 2 and 3 gives 5.
   How we check: a test calls add(2, 3).
2. Adding text gives a plain error.
   How we check: a test passes "a".

## Out of scope
Subtraction.

## Decisions
- Whole numbers only.

## Open questions
- Decimal support. deferred: not needed yet
"""

DESIGN = """# Design

## The picture
1. Read two numbers [script] because parsing is exact work.
2. Add them [script] because arithmetic belongs in code.
3. Write one friendly sentence [AI] because wording needs judgment.

## Where things live
Template in template.md, numbers in data/, rules in rules.toml, logic in scripts/.

## Test data and real data
Tests use tests/fixtures; real runs use data/.

## When something goes wrong
A bad input prints one line and exits non-zero; see .gs/logs.

## Risks
None worth naming.
"""

PLAN = """# Plan

## Summary
Build the adder in two thin phases.

## Phases

### Phase 1: add
Builds: scripts/add.py
Done when: add(2, 3) returns 5
Check: tests/test_add.py

### Phase 2: errors
Builds: error handling
Done when: text input gives a plain error
Check: tests/test_errors.py

## Progress
- [ ] Phase 1
- [ ] Phase 2

## Decision log

## Surprises
"""

TEST_ADD = """import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class T(unittest.TestCase):
    def test_add(self):
        import add
        self.assertEqual(add.add(2, 3), 5)
"""

REPORT = """# Verify report

## Acceptance checks
1. [met] Adding 2 and 3 gives 5. Evidence: tests/test_add.py passes.
2. [met] Text gives a plain error. Evidence: tests/test_errors.py passes.

## Spot check
Result: matched
"""


class GsCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gs-test-")
        self.data = tempfile.mkdtemp(prefix="gs-data-")
        self.env = dict(os.environ, HOME=self.data, USERPROFILE=self.data,
                        GS_STARTER_PATH=os.path.join(self.data, "packs"))
        self.env.pop("CLAUDE_CONFIG_DIR", None)
        self.env.pop("CLAUDE_PROJECT_DIR", None)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.data, ignore_errors=True)

    def gs(self, *args, stdin=None, cwd=None):
        result = subprocess.run([sys.executable, GS] + list(args), cwd=cwd or self.dir, env=self.env,
                                input=(stdin or "").encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return result.returncode, result.stdout.decode("utf-8")

    def hook(self, event, payload):
        payload = dict({"cwd": self.dir, "session_id": "s1"}, **payload)
        code, output = self.gs("hook", event, stdin=json.dumps(payload))
        self.assertEqual(code, 0, output)
        return json.loads(output) if output.strip() else None

    def write(self, rel, text):
        path = os.path.join(self.dir, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def state(self):
        with open(os.path.join(self.dir, ".gs", "state.json"), encoding="utf-8") as handle:
            return json.load(handle)

    def edit(self, rel):
        return self.hook("pre-tool", {"tool_name": "Write", "tool_input": {"file_path": os.path.join(self.dir, rel)}})

    def warned(self, rel):
        """True when the hook advised against this edit. A hook never refuses: it only advises."""
        answer = self.edit(rel)
        if not answer:
            return False
        self.assertNotIn("permissionDecision", answer["hookSpecificOutput"])
        self.assertNotIn("decision", answer)
        return answer["hookSpecificOutput"]["additionalContext"].startswith("gs advice:")

    def to_implement(self):
        self.gs("init", "--name", "adder")
        self.write("docs/explore-notes.md", "notes")
        self.gs("done", "explore")
        self.write("SPEC.md", SPEC)
        self.assertEqual(self.gs("done", "define")[0], 0)
        self.assertEqual(self.gs("approve")[0], 0)
        self.write("docs/design.md", DESIGN)
        self.write("PLAN.md", PLAN)
        code, output = self.gs("done", "design")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.gs("approve")[0], 0)


class TestFlow(GsCase):
    def test_status_outside_project(self):
        code, output = self.gs("status")
        self.assertEqual(code, 1)
        self.assertIn("/gs:1-explore", output)

    def test_init_and_order(self):
        code, output = self.gs("init", "--name", "adder")
        self.assertEqual(code, 0, output)
        self.assertIn("NEXT: /gs:1-explore", output)
        self.assertTrue(os.path.isdir(os.path.join(self.dir, ".git")))
        code, output = self.gs("done", "define")
        self.assertEqual(code, 1)
        self.assertIn("Explore", output)
        code, output = self.gs("done", "explore")
        self.assertEqual(code, 1)
        self.write("docs/explore-notes.md", "notes")
        self.assertEqual(self.gs("done", "explore")[0], 0)
        self.assertEqual(self.state()["stage"], "define")

    def test_init_twice_keeps_state(self):
        self.gs("init", "--name", "adder")
        code, output = self.gs("init", "--name", "other")
        self.assertEqual(code, 0)
        self.assertEqual(self.state()["project"], "adder")

    def test_spec_lint_and_gate(self):
        self.gs("init")
        self.write("docs/explore-notes.md", "notes")
        self.gs("done", "explore")
        self.write("SPEC.md", SPEC.replace("   How we check: a test calls add(2, 3).\n", ""))
        code, output = self.gs("lint", "spec")
        self.assertEqual(code, 1)
        self.assertIn("Acceptance check 1", output)
        self.assertEqual(self.gs("done", "define")[0], 1)
        self.write("SPEC.md", SPEC.replace("deferred: not needed yet", "maybe"))
        self.assertIn("Open question", self.gs("lint", "spec")[1])
        self.write("SPEC.md", SPEC.replace("A small tool", "word " * 130))
        self.assertIn("limit is 120", self.gs("lint", "spec")[1])
        self.write("SPEC.md", SPEC)
        self.assertEqual(self.gs("lint", "spec")[0], 0)
        code, output = self.gs("approve")
        self.assertEqual(code, 1)
        self.assertIn("Nothing is waiting", output)
        self.gs("done", "define")
        self.assertIn("NEXT: /gs:approve", self.gs("status")[1])
        code, output = self.gs("approve", "--note", "fine")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.state()["stage"], "design")

    def test_plan_lint(self):
        self.gs("init")
        self.write("docs/explore-notes.md", "notes")
        self.gs("done", "explore")
        self.write("SPEC.md", SPEC)
        self.gs("done", "define")
        self.gs("approve")
        self.write("docs/design.md", DESIGN.replace(" [script] because arithmetic belongs in code", ""))
        self.write("PLAN.md", PLAN.replace("Done when: add(2, 3) returns 5\n", ""))
        code, output = self.gs("lint", "plan")
        self.assertEqual(code, 1)
        self.assertIn("Step 2", output)
        self.assertIn("Phase 1 has no 'Done when:'", output)

    def test_editing_approved_spec_reopens_gate(self):
        self.to_implement()
        self.assertFalse(self.warned("scripts/add.py"))
        self.write("SPEC.md", SPEC.replace("- Whole numbers only.", "- Whole numbers only.\n- One more decision."))
        self.assertTrue(self.warned("scripts/add.py"))
        output = self.gs("status")[1]
        self.assertIn("changed after approval", output)
        self.assertEqual(self.gs("approve")[0], 0)
        self.assertEqual(self.state()["stage"], "implement")
        self.assertFalse(self.warned("scripts/add.py"))

    def test_progress_ticks_do_not_reopen_plan(self):
        self.to_implement()
        self.write("PLAN.md", PLAN.replace("- [ ] Phase 1", "- [x] Phase 1"))
        self.assertNotIn("changed after approval", self.gs("status")[1])

    def test_phases_check_canary_verdict(self):
        self.to_implement()
        self.assertEqual(self.state()["phases"][0]["name"], "add")
        self.write("tests/test_add.py", TEST_ADD)
        code, output = self.gs("check")
        self.assertEqual(code, 1)
        self.assertIn("CHECK: FAIL", output)
        self.assertEqual(self.gs("done", "implement")[0], 1)
        self.write("scripts/add.py", "def add(a, b):\n    return a + b\n")
        code, output = self.gs("check")
        self.assertEqual(code, 0, output)
        self.assertIn("CHECK: PASS", output)
        code, output = self.gs("canary", "scripts/add.py")
        self.assertEqual(code, 0, output)
        self.assertIn("Canary proved", output)
        with open(os.path.join(self.dir, "scripts", "add.py")) as handle:
            self.assertIn("return a + b", handle.read())
        self.assertEqual(self.gs("done", "implement")[0], 0)
        self.assertTrue(self.warned("scripts/add.py"))  # waiting on the phase gate
        self.gs("revise")
        self.assertFalse(self.warned("scripts/add.py"))
        self.gs("done", "implement")
        self.assertEqual(self.gs("approve")[0], 0)
        self.assertEqual(self.state()["phase"], 2)
        self.gs("done", "implement")
        self.assertEqual(self.gs("approve")[0], 0)
        self.assertEqual(self.state()["stage"], "verify")
        self.assertEqual(self.gs("done", "verify")[0], 1)  # no report yet
        self.write("docs/verify-report.md", REPORT)
        code, output = self.gs("verdict")
        self.assertIn("VERDICT: PROVEN", output)
        self.write("docs/verify-report.md", REPORT.replace("Result: matched", "Result: not done"))
        self.assertIn("PARTLY PROVEN", self.gs("verdict")[1])
        self.write("docs/verify-report.md", REPORT.replace("2. [met]", "2. [not met]"))
        self.assertIn("NOT PROVEN", self.gs("verdict")[1])
        code, output = self.gs("done", "verify")
        self.assertIn("NOT PROVEN", output)
        self.assertIn("NEXT: /gs:fix", self.gs("status")[1])
        self.assertEqual(self.gs("approve")[0], 1)  # NOT PROVEN is not a gate: nothing is waiting
        self.assertFalse(self.warned("scripts/add.py"))  # so a fix can be made
        self.write("docs/verify-report.md", REPORT)
        code, output = self.gs("done", "verify")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.gs("approve")[0], 0)
        self.assertEqual(self.state()["stage"], "deploy")
        self.assertEqual(self.gs("done", "deploy")[0], 1)
        self.write("docs/run-book.md", "how to run")
        self.assertEqual(self.gs("done", "deploy")[0], 0)
        self.assertEqual(self.state()["stage"], "operate")

    def test_canary_catches_a_check_that_cannot_fail(self):
        self.to_implement()
        self.write("tests/test_nothing.py", "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n")
        self.write("scripts/add.py", "def add(a, b):\n    return a + b\n")
        code, output = self.gs("canary", "scripts/add.py")
        self.assertEqual(code, 1)
        self.assertIn("proves nothing", output)

    def test_map_and_guides(self):
        code, output = self.gs("map", cwd=self.data)
        self.assertEqual(code, 0)
        self.assertEqual([line.split()[0] for line in output.splitlines()[1:8]],
                         ["/gs:1-explore", "/gs:2-define", "/gs:3-design", "/gs:4-implement", "/gs:5-verify",
                          "/gs:6-deploy", "/gs:7-operate"])
        self.gs("init")
        self.assertIn("here  /gs:1-explore", self.gs("map")[1])
        self.assertIn("handoff", self.gs("guide")[1])
        code, output = self.gs("guide", "handoff")
        self.assertEqual(code, 0)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", output)
        self.assertEqual(self.gs("guide", "nope")[0], 1)

    def test_change_request(self):
        self.gs("init")
        self.assertIn("docs/changes/001-add-a-weekly-view.md", self.gs("change", "new", "Add a weekly view")[1])
        self.assertIn("002-", self.gs("change", "new", "Another")[1])

    def test_an_open_change_request_points_back_to_define_until_the_spec_is_approved_again(self):
        self.to_implement()
        self.assertIn("NEXT: /gs:2-define", self.gs("change", "new", "Count refunds too")[1])
        self.assertIn("NEXT: /gs:2-define", self.gs("status")[1])
        self.write("SPEC.md", SPEC.replace("- Whole numbers only.", "- Whole numbers only.\n- Refunds count."))
        code, output = self.gs("done", "define")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.gs("approve")[0], 0)
        self.assertNotIn("NEXT: /gs:2-define", self.gs("status")[1])

    def test_doctor(self):
        code, output = self.gs("doctor")
        self.assertEqual(code, 0, output)
        self.assertIn("Automatic reminders: off", output)
        self.assertIn("SETUP: READY", output)
        self.hook("session-start", {})
        self.assertIn("Automatic reminders: on", self.gs("doctor")[1])


class TestHooks(GsCase):
    def test_hooks_are_silent_outside_a_project(self):
        for event in ("session-start", "user-prompt", "pre-tool", "post-tool", "stop"):
            self.assertIsNone(self.hook(event, {"prompt": "hello", "tool_name": "Write",
                                                "tool_input": {"file_path": os.path.join(self.dir, "a.py")}}))

    def test_hook_survives_bad_input(self):
        code, output = self.gs("hook", "pre-tool", stdin="not json")
        self.assertEqual((code, output), (0, ""))

    def test_build_order_advice(self):
        self.gs("init")
        first = self.edit("scripts/add.py")
        self.assertIn("spec has not been approved", first["hookSpecificOutput"]["additionalContext"])
        self.assertIn("/gs:2-define", first["systemMessage"])  # the person is told too, with the usual next step
        self.assertTrue(self.warned("scripts/add.py"))
        self.assertFalse(self.warned("SPEC.md"))
        self.assertFalse(self.warned("docs/explore-notes.md"))
        self.assertFalse(self.warned("data/mail_raw/search.json"))
        self.assertFalse(self.warned("prototype/look.html"))
        self.assertTrue(self.warned(".gs/state.json"))
        outside = self.hook("pre-tool", {"tool_name": "Write", "tool_input": {"file_path": os.path.join(self.data, "x.py")}})
        self.assertIsNone(outside)

    def test_relative_path_and_windows_separators(self):
        self.gs("init")
        answer = self.hook("pre-tool", {"tool_name": "Edit", "tool_input": {"file_path": "scripts/add.py"}})
        self.assertIn("gs advice:", answer["hookSpecificOutput"]["additionalContext"])

    def test_session_start_and_prompt_context(self):
        self.gs("init")
        answer = self.hook("session-start", {})
        self.assertIn("NEXT: /gs:1-explore", answer["hookSpecificOutput"]["additionalContext"])
        answer = self.hook("user-prompt", {"prompt": "what now"})
        self.assertIn("Step 1 of 7: Explore", answer["hookSpecificOutput"]["additionalContext"])

    def test_only_a_typed_approval_approves_when_hooks_are_alive(self):
        self.gs("init")
        self.write("docs/explore-notes.md", "notes")
        self.gs("done", "explore")
        self.write("SPEC.md", SPEC)
        self.gs("done", "define")
        self.hook("user-prompt", {"prompt": "looks good to me"})
        code, output = self.gs("approve")  # the model trying to approve on its own
        self.assertEqual(code, 1)
        self.assertIn("typed approval", output)
        answer = self.hook("user-prompt", {"prompt": "/gs:approve go ahead"})
        self.assertIn("now recorded", answer["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.state()["stage"], "design")
        self.assertEqual(self.state()["gates"]["spec"]["note"], "go ahead")
        self.write("docs/design.md", DESIGN)
        self.write("PLAN.md", PLAN.replace("Builds: scripts/add.py\n", ""))
        self.assertEqual(self.gs("done", "design")[0], 1)
        self.write("PLAN.md", PLAN)
        self.gs("done", "design")
        self.assertEqual(self.gs("approve")[0], 1)
        answer = self.hook("user-prompt", {"prompt": "Approve"})
        self.assertIn("now recorded", answer["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.state()["stage"], "implement")
        answer = self.hook("user-prompt", {"prompt": "approve"})  # nothing waiting: just the reminder
        self.assertNotIn("recorded", answer["hookSpecificOutput"]["additionalContext"])

    def test_typed_approval_that_cannot_be_recorded(self):
        self.to_implement()
        self.write("tests/test_add.py", TEST_ADD)
        self.write("scripts/add.py", "def add(a, b):\n    return a + b\n")
        self.gs("done", "implement")
        self.write("scripts/add.py", "def add(a, b):\n    return a - b - 1000\n")
        self.hook("post-tool", {"tool_name": "Write", "tool_input": {"file_path": os.path.join(self.dir, "scripts/add.py")}})
        answer = self.hook("user-prompt", {"prompt": "/gs:approve"})
        self.assertIn("could not be recorded", answer["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.state()["phase"], 1)

    def test_gs_commands_get_the_full_status(self):
        self.gs("init")
        with open(os.path.join(self.dir, ".claude", "settings.json"), encoding="utf-8") as handle:
            allow = json.load(handle)["permissions"]["allow"]
        self.assertIn("Bash(python *gs.py*)", allow)  # the gs command needs no prompt in a plain-words turn either
        self.assertTrue(all("gs.py" in rule for rule in allow))  # and nothing else is allowed
        code, output = self.gs("hook", "session-start", "--via", "py", stdin="{}")
        self.assertIn('A gs command is run as: py \\"', output)
        answer = self.hook("user-prompt", {"prompt": "/gs:help"})
        self.assertIn("gs project status", answer["hookSpecificOutput"]["additionalContext"])

    def test_stop_hook_runs_the_check(self):
        self.to_implement()
        self.write("tests/test_add.py", TEST_ADD)
        self.write("scripts/add.py", "def add(a, b):\n    return a - b - 1000\n")
        self.assertIsNone(self.hook("stop", {}))  # nothing marked as changed yet
        self.hook("post-tool", {"tool_name": "Write", "tool_input": {"file_path": os.path.join(self.dir, "scripts/add.py")}})
        answer = self.hook("stop", {})
        self.assertNotIn("decision", answer)  # the turn is never held open
        self.assertIn("automatic check fails", answer["systemMessage"])
        self.assertFalse(self.state()["check"]["last"]["ok"])  # the failure is on the record
        prompt = self.hook("user-prompt", {"prompt": "carry on"})
        self.assertIn("last check FAILED", prompt["hookSpecificOutput"]["additionalContext"])
        self.write("scripts/add.py", "def add(a, b):\n    return a + b\n")
        self.assertIsNone(self.hook("stop", {}))
        self.assertIsNone(self.hook("stop", {}))  # clean now, so no check is run


class TestStarter(GsCase):
    def test_starter_copy_and_protection(self):
        starters = os.path.join(self.data, "packs", "zz-test")
        os.makedirs(os.path.join(starters, "tests", "fixtures"), exist_ok=True)
        try:
            with open(os.path.join(starters, "starter.json"), "w") as handle:
                json.dump({"name": "zz-test", "protected_globs": ["tests/fixtures/**", "check.py"],
                           "code_globs": ["scripts/**", "*.py"],
                           "phases": [{"n": 1, "name": "one", "script": "scripts/a.py", "checkpoint": "checkpoints/phase1"}]}, handle)
            with open(os.path.join(starters, "tests", "fixtures", "key.json"), "w") as handle:
                handle.write("{}")
            with open(os.path.join(starters, "check.py"), "w") as handle:
                handle.write("print('CHECK: PASS')\n")
            self.write("check.py", "print('mine')\n")
            code, output = self.gs("init", "--starter", "zz-test")
            self.assertEqual(code, 0, output)
            self.assertIn("already existed", output)
            self.assertFalse(os.path.exists(os.path.join(self.dir, "starter.json")))
            self.assertTrue(self.warned("tests/fixtures/key.json"))
            answer = self.edit("check.py")
            self.assertIn("answer key", answer["hookSpecificOutput"]["additionalContext"])
            self.assertNotIn("systemMessage", answer)  # the person is told once per turn, not on every edit
            self.assertEqual(self.gs("verdict")[1].count("were changed after setup"), 0)
            self.write("tests/fixtures/key.json", '{"changed": true}')
            self.assertIn("tests/fixtures/key.json", self.gs("verdict")[1])  # a changed answer key shows in the verdict
            self.assertEqual(self.gs("init", "--starter", "nope", cwd=self.data)[0], 1)
        finally:
            shutil.rmtree(starters, ignore_errors=True)

    def test_connector_answers_are_saved_only_where_the_starter_asks(self):
        starters = os.path.join(self.data, "packs", "zz-capture")
        os.makedirs(starters, exist_ok=True)
        try:
            with open(os.path.join(starters, "starter.json"), "w") as handle:
                json.dump({"name": "zz-capture", "capture_tools": ["search_threads"], "capture_dir": "data/answers"}, handle)
            self.gs("init", "--starter", "zz-capture")
            call = {"tool_name": "mcp__claude_ai_Gmail__search_threads", "tool_input": {"query": "q"},
                    "tool_response": '{"threads": [{"id": "t1"}]}'}
            answer = self.hook("post-tool", call)
            self.assertIn("gs saved this search_threads answer", answer["hookSpecificOutput"]["additionalContext"])
            with open(os.path.join(self.dir, "data", "answers", "001-search_threads.json"), encoding="utf-8") as handle:
                saved = json.load(handle)
            self.assertEqual(saved["answer"], {"threads": [{"id": "t1"}]})  # exactly as returned, parsed once
            self.assertEqual(saved["input"], {"query": "q"})
            self.hook("post-tool", call)
            self.assertTrue(os.path.exists(os.path.join(self.dir, "data", "answers", "002-search_threads.json")))
            other = dict(call, tool_name="mcp__claude_ai_Gmail__send_message")
            self.assertIsNone(self.hook("post-tool", other))  # a tool the starter did not name is never saved
            self.assertEqual(len(os.listdir(os.path.join(self.dir, "data", "answers"))), 2)
        finally:
            shutil.rmtree(starters, ignore_errors=True)


class TestGeneric(GsCase):
    """The plugin itself names no connected service and no particular project; a starter declares its own needs."""

    WORDS = ("gmail", "calendar", "daily-brief", "daily brief", "fetch-day", "list_events", "search_threads",
             "get_thread", "rules.toml", "workshop", "facilitator", "mailbox", "inbox")

    def plugin_files(self):
        root = os.path.dirname(os.path.dirname(GS))
        for folder in ("skills", "agents", "guides", "hooks", "scripts", "docs", ".claude-plugin"):
            for base, _, names in os.walk(os.path.join(root, folder)):
                for name in names:
                    if name.endswith((".md", ".json", ".py")):
                        yield os.path.join(base, name)
        yield os.path.join(root, "README.md")

    def test_plugin_text_names_no_connector_and_no_particular_project(self):
        found = []
        for path in self.plugin_files():
            with open(path, encoding="utf-8") as handle:
                text = handle.read().lower()
            found += ["%s: %s" % (os.path.relpath(path, os.path.dirname(os.path.dirname(GS))), word)
                      for word in self.WORDS if word in text]
        self.assertEqual(found, [])

    def test_a_starter_can_be_any_folder_given_by_path(self):
        source = tempfile.mkdtemp(prefix="gs-starter-")
        try:
            with open(os.path.join(source, "starter.json"), "w", encoding="utf-8") as handle:
                json.dump({"name": "my-kit", "title": "A kit kept outside the plugin"}, handle)
            with open(os.path.join(source, "README.md"), "w", encoding="utf-8") as handle:
                handle.write("kit\n")
            code, output = self.gs("init", "--starter", source)
            self.assertEqual(code, 0, output)
            self.assertEqual(self.state()["starter"], "my-kit")
            self.assertTrue(os.path.exists(os.path.join(self.dir, "README.md")))
            self.assertFalse(os.path.exists(os.path.join(self.dir, "starter.json")))
        finally:
            shutil.rmtree(source, ignore_errors=True)

    def test_the_plugin_ships_no_starter_and_finds_those_in_other_installed_plugins(self):
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(os.path.dirname(GS)), "starters")))
        self.assertIn("No starters are installed", self.gs("starters")[1])
        pack = os.path.join(self.data, "cache", "some-market", "a-starter-pack", "1.0")
        os.makedirs(os.path.join(pack, "starters", "my-kit"))
        with open(os.path.join(pack, "starters", "my-kit", "starter.json"), "w", encoding="utf-8") as handle:
            json.dump({"name": "my-kit", "title": "A kit from another plugin"}, handle)
        os.makedirs(os.path.join(self.data, ".claude", "plugins"))
        with open(os.path.join(self.data, ".claude", "plugins", "installed_plugins.json"), "w", encoding="utf-8") as handle:
            json.dump({"version": 2, "plugins": {"a-starter-pack@some-market": [{"scope": "user", "installPath": pack}]}}, handle)
        self.assertIn("- my-kit: A kit from another plugin", self.gs("starters")[1])
        code, output = self.gs("init", "--starter", "my-kit")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.state()["starter"], "my-kit")

    def test_a_starter_unpacked_into_the_folder_is_used_where_it_is(self):
        self.write("starter.json", json.dumps({"name": "my-kit", "protected_globs": ["check.py"]}))
        self.write("check.py", "print('CHECK: PASS')\n")
        code, output = self.gs("init")
        self.assertEqual(code, 0, output)
        self.assertIn("used as it is", output)
        self.assertEqual(self.state()["starter"], "my-kit")
        self.assertFalse(os.path.exists(os.path.join(self.dir, "starter.json")))
        self.assertTrue(os.path.exists(os.path.join(self.dir, ".gs", "starter.json")))
        self.assertTrue(self.warned("check.py"))

    def test_a_starter_one_folder_down_gets_a_plain_instruction(self):
        self.write("my-kit/starter.json", json.dumps({"name": "my-kit"}))
        code, output = self.gs("init")
        self.assertEqual(code, 1)
        self.assertIn("one folder down, in 'my-kit'", output)

    def test_a_project_without_a_starter_saves_no_tool_answers_and_names_no_service(self):
        self.gs("init")
        self.hook("post-tool", {"tool_name": "mcp__anything__read_rows", "tool_input": {"q": "x"},
                                "tool_response": "{\"rows\": []}", "cwd": self.dir})
        self.assertFalse(os.path.exists(os.path.join(self.dir, "data")))
        self.assertNotIn("Connected services", self.gs("doctor")[1])


if __name__ == "__main__":
    unittest.main()
