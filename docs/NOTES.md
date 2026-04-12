# Notes: Unit Testing & Environment Setup in Python

Collected highlights from debugging and fixing a broken `pytest` setup. These focus on gotchas that are easy to miss when you're just starting with test frameworks in Python.

---

## 1. pytest auto-collection rules

pytest collects tests by **name convention**, not by decoration:

- Files matching `test_*.py` or `*_test.py`
- Classes starting with `Test` (and without an `__init__` method)
- Functions/methods starting with `test_`

**Gotcha**: naming a *base class* `TestFooCase` makes pytest try to collect it as a real test class — and if it has special methods like `setup`, they can collide with pytest's own hooks. Prefer names like `BaseTestCase`, `XTestCase`, or `FooTestCase` for abstract/base classes that you do **not** want pytest to instantiate.

## 2. `setup` vs `setup_method` (pytest lifecycle)

pytest recognizes several special lifecycle methods on test classes:

- `setup_method(self, method)` — runs before each test method (current/recommended)
- `teardown_method(self, method)` — runs after each test method
- `setup_class(cls)` / `teardown_class(cls)` — once per class
- `setup` / `teardown` — legacy names, still honored

If your base class defines a plain `setup()` that raises `NotImplementedError`, pytest may try to call it automatically if the class is ever collected. Either rename it (e.g., `initialize`) or make sure the class isn't collected (see rule #1).

## 3. `pytest.raises` can hide the wrong exception

```python
with pytest.raises(Exception) as exc:
    TestFooCase().setup()   # NameError: not imported!
assert "Subclasses must implement this method" in str(exc.value)
```

`pytest.raises(Exception)` is **too broad**. Because `NameError` *is* an `Exception`, a missing import inside the block gets silently caught — the assertion then fails on the wrong message, giving a misleading error.

**Rule of thumb**: match the *narrowest* exception you actually expect.

```python
with pytest.raises(NotImplementedError, match="Subclasses must implement"):
    XTestCase().setup()
```

`match=` checks the message via regex — cleaner than a separate `assert`.

## 4. Import hygiene in tests

A test file that references a symbol without importing it will raise `NameError` at runtime — inside any `with` block, that exception *propagates*, not evaluates the reference lazily. Always import what you test explicitly. "The test passes" is only meaningful when the test is actually exercising the code you think it is.

## 5. Refactor blast radius: grep before renaming

Before renaming a class, module, or function:

```bash
# find every reference (ripgrep is faster, but grep -rn works too)
rg -n "TestFooCase" .
```

This tells you:
- How many files are affected
- Whether imports, docs, or serialized data reference the name
- Whether the rename is "surgical" (≤5 refs) or a project-wide refactor

Small rename = safe to do inline. Large rename = consider an LSP-driven rename or a scripted refactor so you don't miss a site.

## 6. PEP 8 naming

| Entity   | Convention   | Example          |
|----------|--------------|------------------|
| Module   | `snake_case` | `xtest_case.py`  |
| Class    | `CapWords`   | `XTestCase`      |
| Function | `snake_case` | `setup_method`   |
| Constant | `UPPER_CASE` | `MAX_RETRIES`    |

The module and the primary class it contains typically share a name — `xtest_case.py` → `XTestCase`. This makes imports read like prose: `from app.xtest_case import XTestCase`.

## 7. pytest path resolution (why "ModuleNotFoundError" happens)

With no `pyproject.toml` / `pytest.ini` / `conftest.py`, pytest uses `importmode=prepend` and picks the **first non-package ancestor** of each test file as the directory added to `sys.path`.

- No `__init__.py` in `src/tests/`? → `src/tests/` itself is the non-package root → `src/tests/` is added to `sys.path`, **not** `src/`
- Result: `from app.xtest_case import XTestCase` fails with `ModuleNotFoundError: No module named 'app'`

### Three ways to fix the import path

| Approach | Where | Tradeoff |
|---|---|---|
| **`pytest.ini` / `pyproject.toml` with `pythonpath = src`** | Repo root | Explicit, modern, standard |
| **Add `__init__.py` to `src/tests/`** | Makes `tests` a package; `src/` becomes the non-package parent and gets added | Implicit, relies on importmode behavior |
| **`PYTHONPATH=src` in the Makefile** | Test target only | Couples test config to build tooling; won't help when running pytest directly |

The **`pytest.ini`** option used here:

```ini
[pytest]
pythonpath = src
testpaths = src/tests
```

- `pythonpath` → prepends `src` to `sys.path` so `app.*` imports resolve
- `testpaths` → makes `pytest` (with no arg) only scan `src/tests/` — faster, avoids accidentally collecting from `.venv/` or notebooks

## 8. A "passing" test can still be wrong

The broken starting test failed with:

```
assert 'Subclasses must implement this method' in "name 'TestFooCase' is not defined"
```

If the assertion had been written more loosely — e.g., `assert exc.value is not None` — the test would have **passed** while testing nothing. A green build is not proof of correctness; it's proof that *whatever you wrote* didn't raise. Always verify the test actually fails when the code is broken (mutation test by hand: comment out the `raise`, does the test fail?).

## 9. Use `pytest.raises(..., match=...)` where possible

```python
# Better:
with pytest.raises(NotImplementedError, match=r"Subclasses must implement"):
    XTestCase().setup()
```

This collapses the "did it raise?" and "was the message right?" checks into one, and makes the test fail *at the right line* with a clear diff.

## 10. Layout that keeps future you happy

```
testing-framework/
├── pyproject.toml             # pytest + black + mypy + bandit config
├── Makefile                   # make test / format / lint / typecheck / check
├── requirements.txt
├── src/
│   ├── app/
│   │   └── xtest_case.py      # production code
│   └── tests/
│       └── test_app.py        # mirror of src/app/ structure
└── .venv/                     # gitignored
```

- `src/` holds *everything the app needs to run*; the `.venv/` is pure tooling.
- Tests mirror the app tree — easy to find the test for any module.
- `pyproject.toml` at the repo root is the single source of truth for all dev-tool config.
- The Makefile stays thin: activate venv + call the tool. No path hacks.

---

## 11. Linting, formatting & type checking toolchain

A modern Python project typically runs four kinds of automated checks:

| Kind | Tool | What it catches |
|---|---|---|
| Formatting | `black` | Style drift, inconsistent whitespace, quotes, line length |
| Security | `bandit` | Hardcoded passwords, shell injection, unsafe deserialization, weak crypto |
| Typing | `mypy` | Wrong types, missing returns, `None` where a value is required |
| Tests | `pytest` | Behavior regressions, missing cases |

### Separation of "mutate" vs "verify"

Formatters have two modes, and you almost always want **two Makefile targets**:

```make
format:       # mutates files — run locally before commit
	black src

lint-black:   # verify only — CI gate, fails on drift
	black --check --diff src
```

Rationale: CI must *fail the build* when formatting drifts — not silently fix it (that would hide the diff the author should have reviewed). Dev machines want the opposite — one command to make the problem go away.

### Bandit and `assert`

Bandit's rule **B101** flags every `assert` statement — because Python strips asserts when run with `-O`, so using asserts for security checks silently disables them in production. Good rule in production code, but **pytest tests use `assert` everywhere**. Fix: exclude the tests directory in `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = [".venv", "src/tests", "src/notebooks"]
```

### mypy strictness dial

`mypy` has a strictness spectrum. From loosest to strictest:

1. **Default** — checks only explicitly-typed code; silent on untyped functions. Low signal, zero friction.
2. **Opt-in flags** — e.g., `warn_unused_ignores`, `warn_redundant_casts`, `strict_equality`. Add one at a time as the codebase matures.
3. **`strict = true`** — turns on ~15 checks at once (`disallow_untyped_defs`, `no_implicit_optional`, `warn_return_any`, etc.). Right for greenfield projects; painful to retrofit.

Our config starts at level 2 — strict enough to catch dead code, loose enough to not require type-annotating every single function on day one.

### Pinning tool versions

Some tools (mypy, pydantic, numpy) ship **compiled** binaries via `mypyc`/`Cython` for speed. Those binaries occasionally segfault on specific glibc/Python/ABI combinations. When this happens:

- **Exit code 139** = SIGSEGV — the kernel killed the process; the tool never ran.
- Don't mask it with `|| true`. That turns a crash into a green build.
- Pin a known-good version in `requirements.txt`: `mypy==1.14.1`.
- Report the bug upstream if you can reproduce it.

**General pinning strategy**: pin exact versions for tools whose *correctness* is load-bearing (type checkers, formatters, test runners). Tolerate `>=` only for libraries whose bugs you'd notice in tests.

### Exit codes carry meaning

| Exit | Meaning |
|---|---|
| 0 | Success |
| 1 | Expected failure (type error, test failure, formatting drift) |
| 2 | Tool misuse (bad CLI flags, missing file) |
| 139 | SIGSEGV — crash, never ignore |

Never blanket-catch non-zero exits. The number tells you what went wrong — mixing "expected failure" with "crash" loses the signal.

---

## 12. `pyproject.toml` is not a Poetry thing

Common misconception: "`pyproject.toml` means Poetry." It doesn't. `pyproject.toml` is a **Python language standard**, introduced years before Poetry became popular.

### The PEPs that defined it

| PEP | Year | What it standardized |
|---|---|---|
| **PEP 518** | 2016 | The file itself + `[build-system]` table |
| **PEP 517** | 2017 | How build backends plug in (setuptools, poetry-core, hatchling, flit, pdm…) |
| **PEP 621** | 2020 | Standard `[project]` metadata — name, version, deps (replaces `setup.py`) |
| **PEP 660** | 2021 | Editable installs via `pyproject.toml` |

None of these mention Poetry. Poetry just happens to be an **early adopter** and a common first encounter for many developers.

### Two independent concerns share the file

1. **Build / packaging** — `[build-system]`, `[project]`. Only matters if you're *publishing a package* to PyPI. Plug in setuptools, poetry-core, hatchling, flit, or pdm here.
2. **Tool configuration** — `[tool.<name>]`. Where dev tools read their settings. **Zero dependency on any build tool**.

In our repo we have **none** of concern #1 (we don't publish a package — we `pip install -r requirements.txt`). We only use concern #2:

```toml
[tool.pytest.ini_options]   # pytest
[tool.black]                # formatter
[tool.mypy]                 # type checker
[tool.bandit]               # security linter
```

### Poetry is just another `[tool.*]` entry

Poetry's config lives under `[tool.poetry]` — structurally identical to `[tool.black]`. Removing Poetry from a project doesn't affect the rest of the file.

### Tools that read `pyproject.toml` with no build concept

`black`, `ruff`, `isort`, `mypy`, `pyright`, `pyre`, `pytest`, `coverage`, `tox`, `bandit`, `pre-commit`, `pip` itself (for `[build-system]`).

### Historical context (why the file exists)

Before PEP 518, each tool invented its own config file:

```
setup.cfg     .flake8     .isort.cfg
mypy.ini      pytest.ini  .coveragerc
tox.ini       .bandit     pyrightconfig.json
```

A single repo could have **10+ dotfiles** just for dev-tool config. PEP 518 consolidated them into one TOML file that humans can read and tools can share. Embrace it — your repo root will thank you.

### Rule of thumb

If a Python tool is actively maintained and released after ~2020, it almost certainly reads config from `pyproject.toml`. Use it whether your packaging story is Poetry, setuptools, hatchling, pdm, or nothing at all.

---

## 13. The Template Method pattern (what we built)

`XTestCase.run()` is a textbook **Template Method**: the base class owns the *algorithm skeleton*, and subclasses override specific hooks.

```python
class XTestCase:
    def run(self):                         # ← the "template method"
        self.setup()                       # hook 1
        getattr(self, self.test_method_name)()  # hook 2 (dynamic dispatch)
        self.tear_down()                   # hook 3

    def setup(self): raise NotImplementedError(...)
    def tear_down(self): raise NotImplementedError(...)
```

### Why this pattern matters

- **The base class enforces the invariant**: every test run is `setup → test → tear_down`, in that order, with nothing skipped. A subclass *cannot* accidentally forget to call `tear_down` because the subclass never controls the sequence.
- **Subclasses only fill in the blanks**: they implement `setup`, `tear_down`, and the actual test methods (`method_a`, `method_b`, …). They never touch `run()`.
- **This is literally how xUnit frameworks work**: JUnit, pyunit/unittest, pytest's class-based tests, Ruby's Test::Unit — all instantiate a test case per method and call a `run`-like entry point that orchestrates the lifecycle. Writing your own makes the underlying machinery legible.

### When to reach for Template Method

- Same ordered steps, different content (test runners, request/response pipelines, ETL jobs)
- You want to *guarantee* cleanup runs even when the middle step is overridden
- You want to add new variants without re-implementing the algorithm

### Alternative: composition over inheritance

Template Method uses inheritance for code reuse, which is rigid. Modern alternatives:

- **Strategy pattern** — pass the "variable parts" as callables/objects to a fixed runner.
- **Context managers** — `with setup(): test()` handles setup/teardown without inheritance.
- **pytest fixtures** — declarative setup/teardown via yield.

Pick Template Method when the *algorithm* is the abstraction you want to reuse, and the variations are small enough that subclassing is clearer than wiring up callables.

---

## 14. Printing is not asserting

A test that runs without raising will **pass**, even if it tests nothing. This is the most common silent failure in a test suite:

```python
def test_my_test_case_methods():
    MyTestCase('method_a').run()   # prints "setup\nmethod_a\ntear_down"
    # ← no assertion. Test passes as long as run() doesn't throw.
```

This is **exploration**, not **testing**. It tells you "the code ran to completion" — nothing about correctness. If `method_a()` were replaced by a no-op, the test would still pass.

### The assertion turns it into a test

```python
def test_my_test_case_methods(capsys):
    MyTestCase('method_a').run()
    captured = capsys.readouterr()
    assert captured.out.splitlines() == ['setup', 'method_a', 'tear_down']
```

Now the test **would fail** if:
- `setup` stopped being called first
- `tear_down` was skipped
- The method dispatch picked the wrong function
- Any of them printed something different

That's three invariants locked in with one assertion — a genuinely useful test.

### Mutation test yourself

Before trusting a test, break the code it covers and confirm the test fails. If it still passes, the test is decorative. This is the same principle behind *mutation testing* tools (`mutmut`, `cosmic-ray`) that automate this check across a whole codebase.

---

## 15. `capsys` — pytest's stdout-capture fixture

`capsys` is a built-in pytest fixture that lets you **assert on captured stdout/stderr** without disabling pytest's capture machinery.

### Basic usage

```python
def test_my_test_case_methods(capsys):
    MyTestCase('method_a').run()
    captured = capsys.readouterr()
    assert captured.out.splitlines() == ['setup', 'method_a', 'tear_down']
```

Just add `capsys` as a parameter and pytest injects it. No imports needed.

### `readouterr()` returns a named tuple

```python
captured = capsys.readouterr()
captured.out    # everything printed to stdout since the last read
captured.err    # everything printed to stderr since the last read
```

Calling `readouterr()` **drains the buffer** — subsequent output is captured fresh. This lets you test sequences of actions independently:

```python
def test_xtest_template_method(capsys):
    MyTestCase('method_a').run()
    assert capsys.readouterr().out.splitlines() == ['setup', 'method_a', 'tear_down']

    MyTestCase('method_b').run()  # buffer already drained above
    assert capsys.readouterr().out.splitlines() == ['setup', 'method_b', 'tear_down']
```

Each `readouterr()` only sees output from that iteration — the previous one's output was already consumed.

### `capsys` variants for different capture needs

| Fixture | Captures |
|---|---|
| `capsys` | `sys.stdout` / `sys.stderr` at the Python level |
| `capfd` | File descriptors 1 & 2 at the OS level — catches output from C extensions, subprocesses |
| `capsysbinary` | Same as `capsys` but returns `bytes` (for non-text output) |
| `capfdbinary` | Same as `capfd` but returns `bytes` |
| `caplog` | Python `logging` module records — different channel than print |

**Rule of thumb**: `capsys` is right 95% of the time. Reach for `capfd` only if you're testing something that writes via C code or via a subprocess.

### Interaction with `-s`

The `-s` flag (`--capture=no`) **breaks `capsys`**: since capture is disabled, `capsys.readouterr()` returns empty strings. If you need both live output and captured assertions, use `-rA` instead of `-s`, or drop the fixture-based assertions when debugging interactively.

### When print-based testing is a smell

Asserting on `print()` output is legitimate for:
- Educational scaffolding (this exercise — prove the Template Method fires in order)
- CLI tools where stdout *is* the contract
- Debugging hooks where the output format is stable

It becomes fragile when:
- `print()` is just informational logging (switch to the `logging` module, test with `caplog`)
- The exact output format changes frequently (test the effect, not the message)
- You're really asserting "the function was called" (use `unittest.mock.Mock`, spy on the method, or refactor to return a value)

### Combine with the verbose Makefile target

For our project:

```bash
make test-verbose   # see live print output during development
make test           # run in silence, rely on capsys assertions
```

Two modes, one test file. `capsys` makes the assertion-based test work cleanly while `-sv` makes the same test readable when you want to watch it happen.

---

## 16. Reading pytest output flags

Three orthogonal flags control what pytest shows you:

| Flag | Effect |
|---|---|
| `-v` / `-vv` | Verbose — print full test names (`path::test_name PASSED`), longer diffs |
| `-s` | Disable stdout capture — `print()` streams live |
| `-rA` | Summary — list captured output per outcome at the end (no live stream) |
| `-x` | Exit on first failure (fail-fast) |
| `--pdb` | Drop into debugger on failure |
| `-k <expr>` | Run only tests matching the name expression |

### Why `-sv` is the debugging default

- `-s` alone → you see prints, but can't tell which test emitted them
- `-v` alone → you see test names, but prints are still captured
- `-sv` → test names anchor the prints, so the timeline is legible

Pytest's design separates *what to run* (`-k`, file paths) from *what to show* (`-v`, `-s`, `-r`). Learning these two axes independently makes the CLI far less intimidating.

---

## 17. `capsys` overrides `-s` — and that's by design

Surprise moment: after adding `capsys` to a test, `make test-verbose` (which passes `-sv`) stops showing `print()` output for that test. Why?

### The rule

| Test requests `capsys`? | `-s` flag? | Where does `print()` go? |
|---|---|---|
| No  | No  | Captured globally, shown only on failure |
| No  | Yes | Streams live to terminal |
| **Yes** | No  | **Into the `capsys` buffer** (not terminal) |
| **Yes** | **Yes** | **Into the `capsys` buffer** (not terminal) — `-s` is overridden |

`-s` turns off *global* capture, but `capsys` installs its own per-test capture because the fixture's contract requires it. If `-s` could empty the buffer, `capsys.readouterr()` would return `''` and the fixture would be useless.

### Why this design matters

The fixture guarantees **deterministic capture** regardless of CLI flags. Without it:
- Test passes locally with `pytest` (capture on → buffer filled → assertion passes)
- Test fails in CI with `pytest -s` (capture off → buffer empty → assertion fails)

A test that's sensitive to invocation flags is a flaky test. `capsys` removes that sensitivity by owning its own capture.

### Escape hatch: `capsys.disabled()`

If you want live prints *inside* a `capsys` test (debugging, one-off trace), wrap that section:

```python
def test_xtest_template_method(capsys):
    with capsys.disabled():
        print("→ iteration start")   # streams live to terminal

    MyTestCase('method_a').run()     # still captured
    assert capsys.readouterr().out.splitlines() == ['setup', 'method_a', 'tear_down']
```

`capsys.disabled()` is a context manager — capture resumes when the block exits. This gives you both worlds in one test.

### Decision tree

- **Need to assert on output?** → use `capsys`, accept that `-s` won't help
- **Need live prints for debugging?** → either drop `capsys` temporarily, or wrap the noisy section in `capsys.disabled()`
- **Want consistent CI behavior?** → always use `capsys` for output tests; never rely on `-s` in CI

---

## 18. A useful `.gitignore` (and the subtle rules inside it)

Most Python `.gitignore` templates cover the basics (`__pycache__/`, `.venv/`, `.coverage`). Three patterns worth understanding beyond the defaults:

### Version-pin files *should* be committed

Files like `.tool-versions` (asdf, mise, rtx), `.nvmrc` (Node), `.python-version` (pyenv) pin interpreter versions for your whole team. **Do not gitignore them.** Their entire purpose is to propagate "use Python 3.11.10" to every contributor. Without them, "works on my machine" bugs re-enter through the environment door.

### `.env` files: ignore the real ones, commit a template

```
.env
.env.*
!.env.example
```

- `.env` → ignored (real secrets)
- `.env.*` → ignores `.env.local`, `.env.production`, etc.
- `!.env.example` → **negation** pattern: un-ignores a template file you commit

The template documents *which* variables exist (with fake/empty values) without leaking real credentials. New contributors copy `.env.example → .env` and fill in their own keys.

**gitignore negation order matters**: `!` re-includes a file only if its *parent directory* hasn't been excluded. So `!subdir/file` won't work if `subdir/` itself is already gitignored.

### List tool cache directories explicitly

```
.pytest_cache/
.mypy_cache/
.ruff_cache/
.tox/
.nox/
```

Tempting to write `.*cache*/` — but:
- Too aggressive: also hides `.vscode/cache/` or any dir with "cache" in its name, including ones you might want tracked
- Fragile: new tools introduce new cache dirs (e.g., `.ruff_cache/` didn't exist before ruff shipped); explicit list forces a conscious decision each time

Explicit is also self-documenting — the `.gitignore` reads like an inventory of your toolchain.

### What **not** to gitignore

- **Lock files** (`requirements.txt`, `poetry.lock`, `Pipfile.lock`, `uv.lock`) — the whole team needs reproducible installs
- **Config files** (`pyproject.toml`, `pytest.ini`, `mypy.ini`) — these *are* the project
- **Editor-agnostic files** like `.editorconfig` — shared settings, commit them
- **Build manifests** (`Makefile`, `tox.ini`, `noxfile.py`) — orchestration belongs in the repo

### Debugging "why isn't git ignoring my file?"

```bash
git check-ignore -v path/to/file   # tells you WHICH .gitignore rule matched
```

If the file is **already tracked**, adding it to `.gitignore` does nothing — you have to remove it first:

```bash
git rm --cached path/to/file       # untrack without deleting from disk
```

Then the gitignore rule starts taking effect on future changes.

### One last pattern: gitignore in subdirectories

You can put a `.gitignore` in any directory, not just the repo root. Rules in a nested `.gitignore` apply relative to *that* directory. Useful when one subdirectory has unique artifacts (e.g., `src/notebooks/.gitignore` ignoring `.ipynb_checkpoints/` locally). Most small projects don't need this — one root-level file covers everything.
