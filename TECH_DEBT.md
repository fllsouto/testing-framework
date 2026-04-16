# Tech Debt & Open Questions

A living map of known weaknesses, unclear behavior, and missing coverage in this mini test framework. Each entry is an **observation**, not a prescription — sometimes the right move is "accept and document", not "fix".

Entries are tagged with severity and impact. Update freely across sessions.

**Legend**:
- 🔴 **High** — silent data loss, incorrect results, or spreads to users
- 🟡 **Medium** — surprising behavior, poor error messages, or blocks future work
- 🟢 **Low** — cosmetic, nice-to-have, or minor polish

---

## Framework-level issues

### TD-01 🔴 `setup()` failures are unhandled

**Observation**: `XTestCase.run()` calls `self.setup()` *before* the try/except. If `setup()` raises, the exception propagates out of `run()`:

- `tear_down` is not called → resource leak
- `result` is not updated → no failure recorded, no error recorded
- Test runner crashes mid-suite

**Scenario to test**: `class Broken(MyTestCase): def setup(self): raise RuntimeError("db down")` — verify `run()` handles it gracefully.

**Possible fixes**: wrap setup in its own try/except; classify setup errors differently from test errors (e.g., `result.add_setup_error(name)`); or fail loud but guarantee tear_down via try/finally.

---

### TD-02 🔴 `tear_down()` failures are unhandled

**Observation**: same as TD-01 but for `tear_down()`. It runs outside any exception handler.

**Scenario to test**: `class Broken(MyTestCase): def tear_down(self): raise RuntimeError("cleanup failed")`. Verify the test result is still valid.

**Possible fixes**: wrap in try/except; log-and-continue so one bad tear_down doesn't poison the rest of the suite.

---

### TD-03 🟡 Exception objects are captured but thrown away

**Observation**:
```python
except AssertionError as e:
    result.add_failure(self.test_method_name)   # `e` unused
except Exception as e:
    result.add_error(self.test_method_name)     # `e` unused
```

The actual exception message and traceback are discarded. Users see *that* a test failed, not *why*. Debugging becomes "reproduce locally and hope it fails the same way".

**Scenario to test**: assert that `result.failures` contains not just names but also error context.

**Possible fixes**: store `(name, exception)` tuples; extract a stack trace via `traceback.format_exc()`; add a `FailureInfo` dataclass.

---

### TD-04 🟡 No `test_finished()` counterpart to `test_started()`

**Observation**: the lifecycle is asymmetric. `test_started()` marks run count, but there's no hook for "test completed, regardless of outcome". This blocks:

- Duration tracking (BONUS_EXES Ex. 8)
- Real-time reporting / progress bars
- Flush logic (e.g., ensuring result is serialized after each test)

**Possible fixes**: add `result.test_finished(name)`; call it in a `finally` block.

---

### TD-05 🟡 `summary()` has a trailing comma

**Observation**:
```python
return (
    f"{self.run_count} {self.RUN_MSG}, "
    f"{str(len(self.failures))} {self.FAILURE_MSG}, "
    f"{str(len(self.errors))} {self.ERROR_MSG}, "   # ← stray trailing ", "
)
```

Example output: `"3 run, 0 failed, 0 error, "` — extra ", " at the end.

**Scenario to test**: assert on exact string (BONUS_EXES Ex. 4).

**Possible fix**: build a list and `", ".join(parts)`.

---

### TD-06 🟡 `XTestResult.__init__` takes `suite_name` but never uses it

**Observation**:
```python
def __init__(self, suite_name=None) -> None:
    self.run_count = 0
    # suite_name is stored nowhere
```

Either the parameter is premature (YAGNI) or the implementation is incomplete. Both are debt.

**Possible fix**: decide whether suite_name is needed. If yes — store and use it in `summary()`. If no — remove the parameter.

---

### TD-07 🟢 Stringly-typed `test_method_name`

**Observation**: `MyTestCase('method_a')` — passing a string means:
- Typos caught at runtime, not at type-check time
- IDE can't auto-refactor the name across call sites
- mypy provides no help

**Scenario to test**: mypy-lint the project with `disallow_untyped_calls = true` and see how much safety is left on the table.

**Possible fix**: accept a bound method reference or a `Callable`; see BONUS_EXES Ex. 11.

---

### TD-08 🟢 No way to skip a test

**Observation**: the framework has no equivalent of pytest's `@pytest.mark.skip`. Every registered test runs.

**Possible fix**: introduce a `SkipTest` exception (see BONUS_EXES Ex. 9) and `result.skipped` list.

---

### TD-09 🟢 No suite composition — one test case at a time

**Observation**: users must manually instantiate each `MyTestCase('method_x')`. There's no `XTestSuite` that iterates over discovered method names.

**Possible fix**: implement an `XTestSuite` (see BONUS_EXES Ex. 7).

---

### TD-10 🟢 No reporter abstraction

**Observation**: `summary()` hardcodes a single output format. Real frameworks support plain-text, JUnit XML, TAP, JSON — chosen at runtime.

**Possible fix**: extract a `Reporter` interface; `summary()` becomes `reporter.format(self)`.

---

## Test coverage gaps

### TC-01 🔴 Error path untested

**Observation**: `run()` has an `except Exception` branch that calls `add_error()`. No test exercises this branch. If someone swapped the order of except clauses (`except Exception` before `except AssertionError`), all failures would silently reclassify as errors — and no test would catch it.

**Scenario to test**: a method that raises `ValueError` must land in `result.errors`, not `result.failures`.

---

### TC-02 🔴 Failure path untested

**Observation**: `add_failure()` is similarly uncovered. Same risk.

**Scenario to test**: a method with `assert False` must land in `result.failures`.

---

### TC-03 🟡 `summary()` format untested

**Observation**: string format is a contract. Not locked in. Refactor risk.

**Scenario to test**: construct an `XTestResult` with known counts; assert the exact string.

---

### TC-04 🟡 `tear_down` execution after failure untested

**Observation**: even if the code works today, there's no regression guard for TD-01 / TD-02.

**Scenario to test**: use `capsys` to verify `"tear_down"` appears in output even when the test method raised.

---

### TC-05 🟡 Multiple runs on one result untested

**Observation**: the whole point of Collecting Parameter is that *many* `run()` calls update *one* `result`. The current test exercises three runs but all with the same outcome (success). No test mixes success + failure + error.

**Scenario to test**: run 5 methods — 2 pass, 2 fail, 1 error. Assert `run_count == 5`, `len(failures) == 2`, `len(errors) == 1`.

---

### TC-06 🟢 No negative tests for framework misuse

**Observation**: what happens if a user does `MyTestCase('nonexistent_method').run(result)`? Right now: `AttributeError` from `getattr`, caught by `except Exception`, registered as error. Is that the intended UX? No test pins it down.

**Scenario to test**: pass an unknown method name; assert it becomes an error (or whatever the decided behavior is).

---

## Tooling & project hygiene

### TH-01 🟡 No CI configuration

**Observation**: `make check` exists locally, but no GitHub Actions / GitLab CI / similar config runs it on every push. Without CI, broken `main` branches ship silently.

**Possible fix**: add `.github/workflows/ci.yml` running `make check`.

---

### TH-02 🟡 No coverage threshold enforced

**Observation**: `pytest-cov` is in `requirements.txt` but never invoked. No coverage report, no threshold.

**Possible fix**: add `make coverage` target running `pytest --cov=src/app --cov-fail-under=80`.

---

### TH-03 🟢 No `conftest.py`

**Observation**: shared fixtures (e.g., a fresh `XTestResult` per test) have nowhere to live. They'd be useful once Ex. 2 / Ex. 5 land.

**Possible fix**: add `src/tests/conftest.py` with a `@pytest.fixture def result(): return XTestResult()`.

---

### TH-04 🟢 No type hints on most methods

**Observation**: `XTestCase.run` has a typed `result: XTestResult`, but `setup`, `tear_down`, `method_a/b/c` are untyped. mypy can't fully verify the framework.

**Possible fix**: add `-> None` returns; enable `disallow_untyped_defs` in `pyproject.toml`.

---

### TH-05 🟢 No pre-commit hooks

**Observation**: `make check` has to be run manually. A pre-commit hook could run black + mypy + bandit before every commit and reject unformatted/unsafe code.

**Possible fix**: add `.pre-commit-config.yaml`; document `pre-commit install` in the README.

---

## How to use this file

- **Reading**: skim for high-severity items (🔴) before planning work. The debt that loses data is worse than the debt that annoys users.
- **Adding**: when a weakness surfaces mid-session, write an entry *immediately*. Debt unrecorded is debt forgotten.
- **Resolving**: when you fix something, delete the entry and note the commit SHA in a `Resolved` section below. This becomes a record of the framework's maturity.

### Resolved

*(Move entries here once fixed. Include the commit SHA and a one-line note.)*
