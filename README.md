# oopsys-python

[![PyPI](https://img.shields.io/pypi/v/oopsys-python)](https://pypi.org/project/oopsys-python/)
[![Python](https://img.shields.io/pypi/pyversions/oopsys-python)](https://pypi.org/project/oopsys-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/morington/oopsys-python/blob/main/LICENSE)

> oops, system crashed :)

---

## Table of contents

**About**

- [About the library](#about-the-library)
- [What the library does](#what-the-library-does)
- [Installation](#installation)
- [Quick start](#quick-start)

**API reference**

- [API reference — overview](#api-reference)
- [configure()](#configure)
- [guard](#guard)
- [fallback — what to return on error](#fallback)
- [timeit](#timeit)
- [ignore](#ignore)
- [install()](#install)
- [OOPSYS_LOGGER_NAME](#oopsys_logger_name)
- [Severity](#severity)
- [ErrorReport](#errorreport)

**Practice**

- [Settings (env)](#settings-env)
- [Startup order](#startup-order)
- [Usage scenarios](#usage-scenarios)
- [Examples in the repository](#examples-in-the-repository)

**Other**

- [Publishing to PyPI](#publishing-to-pypi)

---

## About the library

`oopsys-python` catches exceptions in your Python code instead of
crashing the whole process.

**What happens on error:**

1. The exception is caught (if the function is under `@guard` or `install()` is active).
2. An **error** or **critical** entry is written to structlog (channel `OOPSYS`).
3. Optionally a JSON report is sent to an HTTP agent.
4. Caller code receives **`fallback`** (e.g. `None`) — no `raise` and no
   traceback in the application console.

**What oopsys does not do:**

- does not read project env without the `OOPSYS_` prefix, does not manage app configuration;
- does not configure `structlog`;
- does not catch `KeyboardInterrupt` / `SystemExit` (Ctrl+C works as usual).

Sync and async are detected automatically.

---

## What the library does

| Capability | How to enable | Why |
|-------------|--------------|--------|
| Don't crash on function error | `@guard` | Worker, HTTP, parser — loop keeps running |
| Return a value instead of raising | `@guard(fallback=...)` | `if result is None` without try/except |
| Measure call duration (dev) | `@timeit` | DEBUG log `ms` (milliseconds) and `hf` (human-friendly) |
| Skip a function | `@ignore` | Error propagates as without oopsys |
| Catch "forgotten" exceptions | `install()` | Critical in log/agent (optional) |
| Report to agent | `OOPSYS_AGENT__ENABLED=true` | Monitoring outside the app |
| Log only, no agent | `OOPSYS_AGENT__ENABLED=false` | Local debugging |
| Dev: log then raise again | `OOPSYS_RERAISE=true` | See traceback while developing |

---

## Installation

Repository: https://github.com/morington/oopsys-python

### PyPI

```
uv add oopsys-python
```

### GitHub (`main` branch)

```
uv add "oopsys-python @ git+https://github.com/morington/oopsys-python.git"
```

### GitHub (specific tag)

```
uv add "oopsys-python @ git+https://github.com/morington/oopsys-python.git@v0.1.0"
```

---

## Quick start

**1.** Copy [`.env.example`](.env.example) → `.env`.

**2.** In your `structlog` configuration add the `OOPSYS` channel (see [OOPSYS_LOGGER_NAME](#oopsys_logger_name)). Easiest with `kitstructlog`.

**3.** In `main`:

```python
from oopsys_python import configure, guard

from myapp.configuration import Configuration, Loggers


@guard(fallback=None)
async def worker() -> str:
    return await do_work()


async def main() -> None:
    app = Configuration()  # plain pydantic-settings configuration
    Loggers(developer_mode=app.is_development)  # kitstructlog

    configure()
    result = await worker()
    if result is None:
        return  # error already logged
```

---

## API reference

Briefly: what to call, what to put on functions, what to import only for reference.

---

### configure()

**Purpose:** enable oopsys once per process.

**Usage:**

```python
configure()
```

- Reads `.env` / variables with the `OOPSYS_` prefix ([list](#settings-env)).
- Call **after** `Loggers(...)`, **before** guarded functions.
- Does not touch logging setup.

There is no settings class in the public import.

---

### guard

**Purpose:** main decorator — an error inside the function does not crash the program.

**Usage:**

```python
@guard
@guard(fallback=None)
@guard(critical=True, reraise=False)
async def fetch() -> dict | None:
    ...
```

| Outcome | Result |
|-------|-----------|
| Success | Normal `return` |
| Error | Log + optional agent + return `fallback` |
| `reraise=True` | Log and `raise` again |
| Ctrl+C | Not handled by oopsys |

**Where to apply:** `main`, loop worker, `create_task`, scheduler job — not on
every small helper.

Parameters: `fallback`, `critical`, `reraise` — see [fallback](#fallback).

---

### fallback

**Purpose:** what the function **returns** if an exception occurred inside.

Default is `fallback=None`.

```python
@guard(fallback=None)
async def load() -> dict | None:
    return await api.get_json()

data = await load()
if data is None:
    ...  # failure already in OOPSYS log
```

| `fallback` | When it fits |
|------------|----------------|
| `None` | "No data" → `if x is None` |
| `False` | Function returns bool |
| `[]`, `{}` | Empty result (prefer `None` + create a new list yourself) |
| `{"ok": False}` | Single "error" API response shape |

This is **not** a callback: `fallback=lambda: []` will not be called.

Same `fallback` for any error; check the log for type (`error_type`,
`detail`).

---

### timeit

**Purpose:** in development, log call duration.

```python
@timeit
@timeit(label="fetch")
def work() -> None:
    ...
```

- Level **DEBUG**, channel `OOPSYS`.
- Fields: `ms=69.15`, `hf=0:00:00.0692`.
- Only when `OOPSYS_IS_DEVELOPMENT=true`; no-op in prod.

With `guard`:

```python
@guard(fallback=None)
@timeit
async def fetch_fact() -> str:
    ...
```

---

### ignore

**Purpose:** exclude a function from oopsys handling.

```python
@ignore
def strict_check() -> None:
    raise ValueError("must propagate")
```

Such exceptions are not swallowed by `@guard` or caught by `install()`.

---

### install()

**Purpose:** safety net for unhandled exceptions.

```python
configure()
install()
```

Catches "leaks" in the main thread, threads, asyncio → **critical** log + agent.

Does not replace `@guard` for long-running loops.

---

### OOPSYS_LOGGER_NAME

#### (_**Example for kitstructlog**_)

**Purpose:** constant `"OOPSYS"` — logger name for `LoggerReg`.

```python
from kitstructlog import InitLoggers, LoggerReg
from oopsys_python import OOPSYS_LOGGER_NAME

class Loggers(InitLoggers):
    main = LoggerReg(name="MAIN", level=LoggerReg.Level.INFO)
    oopsys = LoggerReg(name=OOPSYS_LOGGER_NAME, level=LoggerReg.Level.INFO)
```

Different name: `OOPSYS_LOGGER_NAME=...` in `.env` and the same `name` in `LoggerReg`.

Levels (DEBUG, ERROR, …) are set in `Loggers`.

---

### Severity

**Purpose:** severity level in the agent report.

| Value | When |
|----------|--------|
| `Severity.ERROR` | Error in `@guard`, process still alive |
| `Severity.CRITICAL` | `install()` or `@guard(critical=True)` |

You usually don't set this in code — oopsys assigns it.

---

### ErrorReport

**Purpose:** JSON report model for the agent and tests.

Fields: `severity`, `service`, `environment`, `exception_type`, `message`,
`traceback`, `timestamp`, `context`.

```json
{
  "severity": "error",
  "service": "my-app",
  "environment": "production",
  "exception_type": "ValueError",
  "message": "invalid literal for int()",
  "traceback": "...",
  "timestamp": "2026-06-01T12:00:00Z",
  "context": {"callable": "compute"}
}
```

You don't need to construct it manually.

---

## Settings (env)

Only the **`OOPSYS_`** prefix. Template: [`.env.example`](.env.example).

```env
OOPSYS_IS_DEVELOPMENT=false
OOPSYS_SERVICE_NAME=app
OOPSYS_LOGGER_NAME=OOPSYS
OOPSYS_RERAISE=false

OOPSYS_AGENT__ENABLED=false
OOPSYS_AGENT__HOST=localhost
OOPSYS_AGENT__PORT=8080
OOPSYS_AGENT__PATH=/reports
OOPSYS_AGENT__TIMEOUT=3.0
```

| Variable | Effect |
|------------|--------|
| `OOPSYS_IS_DEVELOPMENT` | `timeit`, `environment` in report |
| `OOPSYS_SERVICE_NAME` | Name in JSON |
| `OOPSYS_LOGGER_NAME` | structlog channel |
| `OOPSYS_RERAISE` | `raise` again after log |
| `OOPSYS_AGENT__ENABLED` | `false` — log only |
| `OOPSYS_AGENT__*` | Agent URL and timeout |

Agent delivery failure does not crash the application.

---

## Startup order

1. `.env` with `OOPSYS_*` (from `.env.example`).
2. In `Loggers` — channel [OOPSYS_LOGGER_NAME](#oopsys_logger_name).
3. `Loggers(...)` → [configure()](#configure) → optionally [install()](#install).
4. On workers — [guard](#guard) (+ [timeit](#timeit) in dev).
5. After call — check [fallback](#fallback) (`if result is None`).

---

## Usage scenarios

### Long-running worker (parser, polling)

Network fails — iteration returns `None`, loop does not stop.

```python
@guard(fallback=None)
@timeit
async def fetch_fact() -> str:
    ...

async def main() -> None:
    configure()
    while True:
        fact = await fetch_fact()
        if fact is None:
            await asyncio.sleep(5)
            continue
        logger.info("fact", fact=fact)
        await asyncio.sleep(15)
```

Example: [`examples/parser.py`](examples/parser.py).

### Sync script with bad input

Each `compute` call is isolated — one invalid line does not stop the whole run.

```python
@guard(fallback=None)
@timeit
def compute(expr: str) -> int | None:
    ...

for expr in expressions:
    if (r := compute(expr)) is not None:
        logger.info("result", result=r)
```

Example: [`examples/protected_sync.py`](examples/protected_sync.py).

### Async + install + ignore

```python
configure()
install()

@guard(fallback=None)
async def divide(a, b): ...

@ignore
async def must_fail(): ...
```

Example: [`examples/protected_async.py`](examples/protected_async.py).

### Scheduler (APScheduler and similar)

```python
@guard(fallback=None)
async def scheduled_job() -> None:
    ...

scheduler.add_job(scheduled_job, "interval", seconds=30)
```

One job failure — next tick runs on schedule.

### CLI: single run under guard

```python
@guard(critical=True)
def main() -> None:
    ...

if __name__ == "__main__":
    configure()
    main()
```

### Log only, no agent

In `.env`: `OOPSYS_AGENT__ENABLED=false`. Errors in `OOPSYS` channel, no HTTP.

### Dev: see traceback after log

`OOPSYS_RERAISE=true` or `@guard(reraise=True)`.

---

## Examples in the repository

```bash
cp .env.example .env
uv run python examples/protected_sync.py
uv run python examples/protected_async.py
uv run python examples/parser.py
```

| File | Demonstrates |
|------|----------------|
| `protected_sync.py` | `guard`, `timeit`, sync |
| `protected_async.py` | `guard`, `ignore`, `install` |
| `parser.py` | loop, HTTP, `fallback=None` |
