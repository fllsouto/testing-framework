# Bonus Exercises

Derived from the patterns, failures, and design decisions encountered while building this mini xUnit framework. Each exercise has:

- **Goal** — what you're practicing
- **Context** — why it matters
- **Hint** — a nudge, not a solution
- **Stretch** — optional deepening

Exercises are roughly ordered from "direct follow-up" to "wholly new territory". Do them in any order that interests you.

---

## Progress tracker

| # | Title | Status |
|---|---|---|
| 1 | Finish the Collecting Parameter test | ✅ Done |
| 2 | Test the failure path | ✅ Done |
| 3 | Mutation test your framework | ⏳ Open |
| 4 | Assert on `summary()` | ✅ Done (also fixed trailing-comma bug) |
| 5 | Does `tear_down` run when a test fails? | ⏳ Open (partial — spy covers happy path) |
| 6 | Split with `pytest.mark.parametrize` | ⏳ Open |
| 7 | Build an `XTestSuite` | ✅ Done (+ bonus: `XTestLoader`) |
| 8 | Duration tracking | ⏳ Open |
| 9 | TDD skipping | ⏳ Open |
| 10 | try/finally for tear_down | ⏳ Open |
| 11 | Replace stringly-typed names | ⏳ Open |
| 12 | Rich failure messages | ⏳ Open (partial — logging added) |
| 13 | Negative tests for assertion mixin | ⏳ Open |
| 14 | Cooperative `__init__` in `XTestSpy` | ⏳ Open |
| 15 | Close `XTestLoader` edge-case coverage | ⏳ Open |
| 16 | Fix the Bandit B101 warning intentionally | ⏳ Open |
| 17 | Wire `suite_name` through to `summary()` | ⏳ Open |
| 18 | Add a `Reporter` abstraction | ⏳ Open |
| 19 | TDD a `test_finished` lifecycle hook | ⏳ Open |
| 20 | Document the Composite pattern in code | ⏳ Open |

---

## Ex. 1 — Finish the Collecting Parameter test

**Goal**: complete `test_xtest_template_method` after the `run(result)` signature change.

**Context**: the scaffold in conversation §"Collecting Parameter" left you with a `result = XTestResult()` instance and three `run(result)` calls. You need to assert both **lifecycle** (via `capsys`) and **collector state** (via `result`).

**Hint**:
- Three successful runs → what should `result.run_count` be?
- No method raises → `result.failures` and `result.errors` should be …?
- `capsys.readouterr().out.splitlines()` gives you *all* buffered prints from *all three* runs — in order.

**Stretch**: split into two tests — one for lifecycle, one for collector state. Compare readability. Which failure message would be more useful when a regression hits?

---

## Ex. 2 — Test the failure path

**Goal**: verify `XTestResult.failures` actually captures failing methods.

**Context**: your current `MyTestCase` only has methods that pass (they just `print()`). The framework's `add_failure` / `add_error` code paths are **entirely untested**. A framework that claims to collect failures should have tests proving it does.

**Hint**:
1. Add a new method to `MyTestCase` (or a new subclass) that raises `AssertionError` — e.g., `method_fails` that does `assert False, "intentional"`.
2. `run(result)` on it.
3. Assert `'method_fails' in result.failures` and `result.run_count == 1`.

**Stretch**: do the same for a method that raises `ValueError` — should end up in `result.errors`, not `result.failures`. Why the distinction? (Think: `assert` represents a test expectation; other exceptions represent *bugs*.)

---

## Ex. 3 — Mutation test your framework

**Goal**: prove each test fails when the code it claims to cover is broken.

**Context**: from §14 of NOTES.md — a passing test is only meaningful if it *would* fail when the code misbehaves. You can't fully trust a test you haven't seen fail.

**Hint**: for each existing test, break the code one line at a time:
- Comment out `result.test_started()` in `run()`. Does any test fail? Which one?
- Replace `add_failure` with `add_error` in `run()`'s `except AssertionError` branch. Does any test fail?
- Remove the `self.tear_down()` call. Does any test catch it?

**Stretch**: keep a table (code change → test that catches it). Gaps in the table = untested invariants.

---

## Ex. 4 — Assert on `summary()`

**Goal**: pin down the format of `XTestResult.summary()`.

**Context**: `summary()` produces a user-facing string. Its format is a *contract* — callers might parse it, log it, or assert against it downstream. Right now, nothing locks that format in.

**Hint**:
- Run three passing methods, one failing method, one erroring method.
- Assert the exact string returned by `summary()`.
- Notice the trailing comma in the current implementation — `"5 run, 1 failed, 1 error, "`. Is that intentional?

**Stretch**: if you think the trailing comma is a bug, write the test *first* for the format you want (no trailing comma), watch it fail, then fix `summary()`. That's **test-driven development** in miniature.

---

## Ex. 5 — Does `tear_down` run when a test fails?

**Goal**: verify cleanup happens even when the test method raises.

**Context**: this is the whole point of having a tear_down hook. If tear_down is skipped on failure, database transactions leak, temp files pile up, mocks stay installed. Your framework needs to guarantee it — *and prove it*.

**Hint**:
1. Make a test method that raises `AssertionError`.
2. Before asserting on `result`, assert via `capsys` that `"tear_down"` appears in the output even though the test failed.
3. Read `run()` carefully — does it currently call `tear_down()` after an exception? Trace the control flow.

**Stretch**: what happens if **`setup`** raises? Trace it. Is `tear_down` called? Is the exception counted? If you think the answer is "no, this is broken" — add this to `TECH_DEBT.md` (Ex. 9 below lists it as a known gap).

---

## Ex. 6 — Split the test with `pytest.mark.parametrize`

**Goal**: eliminate copy-paste across `method_a/b/c` test cases.

**Context**: your current test repeats three nearly-identical `run()` + assertion blocks. `parametrize` turns this into one test that runs once per parameter, with separate PASS/FAIL reporting for each.

**Hint**:
```python
@pytest.mark.parametrize("method", ["method_a", "method_b", "method_c"])
def test_xtest_template_method(capsys, method):
    result = XTestResult()
    MyTestCase(method).run(result)
    assert capsys.readouterr().out.splitlines() == ["setup", method, "tear_down"]
```

**Stretch**: add `ids=` to parametrize so pytest reports `test_xtest_template_method[method_a]` with custom names. Then add a failing case as a separate parametrize entry that expects `result.failures` to contain the method name.

---

## Ex. 7 — Build an `XTestSuite`

**Goal**: run many `XTestCase` instances with one collector.

**Context**: the real power of Collecting Parameter shows up when you have a *suite* of tests. Right now, your test manually creates `MyTestCase('method_a')`, `MyTestCase('method_b')`, etc. A suite class should auto-discover methods starting with `method_` and run them all.

**Hint**:
```python
class XTestSuite:
    def __init__(self, test_case_class):
        self.test_case_class = test_case_class

    def run(self, result):
        # TODO: use dir() or inspect to find all methods starting with 'method_'
        # then instantiate test_case_class(method_name).run(result) for each.
```

**Stretch**:
- How do you decide *which* methods to auto-discover? (Python convention: `test_*` — pytest's rule.)
- What if a test case has many inherited methods that aren't tests? (Filter by defining class.)

---

## Ex. 8 — Add duration tracking

**Goal**: measure how long each test takes and collect durations in `XTestResult`.

**Context**: slow tests are a real problem at scale. Your framework could record duration per test for later reporting.

**Hint**:
- Use `time.perf_counter()` before `setup()` and after `tear_down()`.
- Store `{test_name: duration_seconds}` in the result.
- Assert that duration is recorded (use a fake slow method with `time.sleep(0.01)`).

**Stretch**: add `result.slowest(n)` that returns the n slowest tests. Pytest does this with `-vv --durations=10`.

---

## Ex. 9 — TDD a new feature: test skipping

**Goal**: add a `skip` mechanism to the framework.

**Context**: real test frameworks let you mark tests as skipped without running them (pytest's `@pytest.mark.skip`, JUnit's `@Ignore`). Start with the test, not the code.

**Hint** (writing the test first):
```python
def test_skip_is_not_counted_as_run():
    # 1. Create a MyTestCase subclass with a method that raises `SkipTest`
    #    (a custom exception you'll need to define).
    # 2. run() on it.
    # 3. Assert: result.run_count == 0 (skipped != run)
    # 4. Assert: result.skipped == ['method_name']
```

Then implement: define `SkipTest`, catch it in `run()`, add `result.add_skip()` / `result.skipped = []`.

**Stretch**: should `skip` prevent `setup` and `tear_down` from running? Look at how pytest handles this. Document the decision in your code.

---

## Ex. 10 — Refactor `run()` to use `try/finally`

**Goal**: guarantee `tear_down()` always runs, even if something inside the try/except itself raises.

**Context**: the current `run()` has a subtle issue — if `result.add_failure()` itself throws (say, because `result.failures` wasn't a list), `tear_down` gets skipped. `try/finally` makes the guarantee unconditional.

**Hint**:
```python
def run(self, result):
    result.test_started()
    self.setup()
    try:
        # ... dispatch test method, catch failures/errors ...
    finally:
        self.tear_down()
```

Write the test first: inject a broken `result` that raises when `add_failure` is called. Assert `tear_down` still ran (check `capsys`).

**Stretch**: what if `setup()` raises? Should the test count as `error`? Wrap setup in its own try too, and think about how failures in setup vs tear_down should be classified.

---

## Ex. 11 — Replace stringly-typed `test_method_name`

**Goal**: get type-checker help for method names.

**Context**: `MyTestCase('method_a')` — pass a string, let `getattr` resolve it at runtime. Typo → `AttributeError` at run time, not at type-check time. Mypy can't catch `MyTestCase('metho_a')`.

**Hint**: refactor to take a *bound method* or a *callable*:
```python
case = MyTestCase()
case.run(result, test=case.method_a)   # IDE autocomplete, mypy checks
```

**Stretch**: compare the two APIs. Which feels more natural for users? Which is easier to auto-discover in a suite? Sometimes stringly-typed is the right choice — write down *why* in a comment.

---

## Ex. 12 — Write a test that fails meaningfully

**Goal**: practice producing good failure messages.

**Context**: a bad assertion: `assert result.run_count == 3`. When it fails, pytest shows `assert 2 == 3`. You have to go find the test to learn what `result.run_count` even represents.

Compare with:
```python
assert result.run_count == 3, (
    f"expected 3 successful runs, got {result.run_count} — "
    f"failures={result.failures}, errors={result.errors}"
)
```

When this fails, you know *immediately* what's wrong.

**Hint**: rewrite one of your existing tests with rich failure messages. Trigger the failure on purpose (break the code) and read the new output.

**Stretch**: use pytest's `pytest.fail("message")` for custom failures, and `pytest.approx(...)` for float comparisons. When would you use each?

---

## Ex. 13 — Negative tests for `XTestAssertionMixin`

**Goal**: prove the assertions raise when they should.

**Context**: `test_assert_equal` currently only checks that matching pairs *don't* raise (`self.assert_equal("foo", "foo")`). But the whole point of `assert_equal` is that it *should* raise `AssertionError` when inputs differ. That half of the contract is untested — if you replaced the body of `assert_equal` with `pass`, your current tests would still pass.

**Hint**:
```python
def test_assert_equal_fails_on_mismatch(self):
    try:
        self.assert_equal("foo", "bar")
    except AssertionError as e:
        self.assert_in("foo != bar", str(e))
        return
    raise AssertionError("expected assert_equal to raise")
```

Write one for each mixin method (`assert_true(False)`, `assert_false(True)`, `assert_in("x", "y")`).

**Stretch**: notice you had to write a tiny "expected failure" dance by hand. This is exactly what pytest's `pytest.raises(...)` context manager does — your framework now has a reason to add an `assert_raises` helper to the mixin.

---

## Ex. 14 — Make `XTestSpy` constructor cooperative

**Goal**: replace `XTestCase.__init__(self, name)` with `super().__init__(name)`.

**Context**: `XTestSpy.__init__` currently calls `XTestCase.__init__(self, name)` explicitly — that's the "old Python" style. Modern cooperative inheritance uses `super()` so that if a third class (a mixin, say) is inserted into the MRO later, initialization still chains correctly. This directly reinforces the Mixin pattern notes in NOTES.md §19.

**Hint**:
```python
class XTestSpy(XTestCase):
    def __init__(self, name):
        super().__init__(name)          # ← cooperative
        self.was_run = False
        # …
```

Then: add a hypothetical `LoggingMixin` that also defines `__init__` and calls `super().__init__(*args, **kwargs)`. Insert it before `XTestCase` in the MRO. Everything still works.

**Stretch**: inspect `XTestSpy.__mro__` in a REPL. Trace how `super().__init__` would walk the chain if you added the mixin.

---

## Ex. 15 — Close the `XTestLoader` edge-case coverage

**Goal**: add tests for cases your loader doesn't currently exercise.

**Context**: `XTestLoaderTest` covers the happy path (a class with `test_*` methods) and one zero-methods case. Gaps:

- A class that inherits test methods from a parent — are inherited methods discovered?
- A class with a method named exactly `"test"` — is it included? (prefix match, not regex)
- A class where a method is spelled `Test_foo` (wrong case)
- The `debug=True` branch of `__init__` — prints are generated but no test exercises it

**Hint**: for each case, add a fixture class and assert on the list returned by `get_test_case_names`. Use `capsys` for the debug-path test.

**Stretch**: these gaps matter if someone extends your framework with `DebugLoader(XTestLoader)` overriding behavior. Untested edges become surprises.

---

## Ex. 16 — Resolve the Bandit B101 warning *intentionally*

**Goal**: pick a strategy for `XTestStub`'s bare `assert`s and document it.

**Context**: Bandit flags `assert True` / `assert False` in `XTestStub` because Python's `-O` optimizer strips them. In production code this is a real bug. In *test fixture* code that *must produce specific outcomes*, it's a false positive. Three honest options:

1. **Local suppression**: `assert False  # nosec B101  (fixture: must raise)` — precise, documents why
2. **File-level exclusion**: add `src/app/xtest_stub.py` to `exclude_dirs` in `pyproject.toml`
3. **Refactor**: replace `assert False` with `raise AssertionError` — works because `XTestCase.run()` catches `AssertionError`

**Hint**: think about which option best expresses "this *is* meant to be a failing test case, not a bug". The answer isn't obvious — it depends on whether you want readers to understand the intent when they look at the line.

**Stretch**: whichever option you pick, remove TD-17 from `TECH_DEBT.md` and add a note to `NOTES.md` explaining your reasoning. Security tool warnings are **dialogs**, not orders.

---

## Ex. 17 — Wire `suite_name` into `summary()`

**Goal**: either use `XTestResult(suite_name=...)` or delete the parameter.

**Context**: TD-06 in `TECH_DEBT.md`. The parameter exists but nothing reads it. This is Chekhov's Gun — if a parameter is documented, the reader expects it to matter. Either it does, or it shouldn't exist.

**Hint**:
- If you keep it: `summary()` could return `"[suite_name] 4 run, 0 failed, 0 error."`
- Your existing summary-assertion tests will fail when the format changes — exactly the right feedback. Update them deliberately.

**Stretch**: related API question — should `XTestRunner.__init__` accept a suite_name too, and forward it to `XTestResult`? Or is suite_name the caller's responsibility?

---

## Ex. 18 — Add a `Reporter` abstraction

**Goal**: decouple result formatting from `XTestResult`.

**Context**: `summary()` hardcodes plain-text. TD-10 in `TECH_DEBT.md`. Real frameworks output plain-text, JUnit XML, TAP, JSON — picked at runtime by the CI system consuming the output.

**Hint**:
```python
class Reporter:
    def format(self, result: XTestResult) -> str: ...

class PlainReporter(Reporter):
    def format(self, result): return f"{result.run_count} run, …"

class JSONReporter(Reporter):
    def format(self, result): return json.dumps(vars(result))
```

`XTestRunner.__init__(reporter=PlainReporter())` — inject the formatter. Default unchanged.

**Stretch**: JUnit XML format is widely consumed by CI. Write a `JUnitReporter`. Your framework just became useful to anyone with a Jenkins install.

---

## Ex. 19 — TDD a `test_finished` lifecycle hook

**Goal**: add the missing lifecycle symmetry. Write the test first.

**Context**: TD-04 — `XTestResult.test_started()` exists but there's no `test_finished()`. Without it, duration tracking, streaming reporters, and per-test flush logic are all blocked.

**Hint** (TDD red phase):
```python
def test_test_finished_is_called(self):
    spy_result = … # a fake/mock result that records invocations
    case = XTestSpy("test_method")
    case.run(spy_result)
    self.assert_equal(
        spy_result.lifecycle_calls,
        ["test_started", "test_finished"]
    )
```

Watch the test fail. Then implement `test_finished()` on `XTestResult` and call it from `XTestCase.run()` in a `finally:` block (so it fires even after failures). Watch the test pass.

**Stretch**: now implement Ex. 8 (duration tracking) — `test_finished()` is the natural place to compute `duration = time.perf_counter() - start`.

---

## Ex. 20 — Document the Composite pattern inside `XTestSuite`

**Goal**: write a short doc-comment explaining why `XTestSuite.run(result)` and `XTestCase.run(result)` share the same signature.

**Context**: you built the Composite pattern (NOTES.md §20) by intuition — suite and case are interchangeable because they both expose `.run(result)`. Documenting the *why* turns an implicit contract into an explicit one. Future contributors (including future you) will see it and not accidentally break the interchangeability by adding a required parameter to one side.

**Hint**: two lines, not two paragraphs:

```python
class XTestSuite:
    """Composite of XTestCase. Leaf and branch share .run(result) so a suite
    can contain suites — see NOTES.md §20."""
```

**Stretch**: add a runtime check — `XTestSuite.add_test` could verify the added object has a `.run` attribute callable with `(result,)`. Gentle structural typing. Decide whether the defensive check is worth the noise. (Most of the time, it isn't — this is a deliberate exercise in saying "no, duck typing is fine".)
