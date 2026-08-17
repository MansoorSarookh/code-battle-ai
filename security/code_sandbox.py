"""
Restricted local code executor for the Code-Writing / Final Boss round.

READ THIS BEFORE DEPLOYING ANYWHERE PUBLIC:
This is a *best-effort* restriction (timeout + a stripped-down builtins/globals
dict), suitable for a single local user testing their own code in their own
hot-seat game. It is explicitly NOT a real sandbox — there is no process
isolation, no memory limit, no filesystem/network jail. Python's `exec` cannot
be made fully safe against a determined attacker no matter how you restrict
builtins (reflection makes most blocklists escapable).

For a real multiplayer/public deployment, replace `run_user_function` below
with a call out to an isolated worker: a gVisor/Firecracker microVM, a locked
down Docker container (`--network none`, read-only fs, cpu/mem cgroup limits,
non-root user, seccomp profile), or a hosted code-execution API. The call
signature (function name, args, expected output) is designed to be a drop-in
swap for such a backend.
"""
from __future__ import annotations

import multiprocessing as mp
import traceback
from typing import Any


import builtins as _builtins_module

_ALLOWED_BUILTIN_NAMES = [
    "len", "range", "min", "max", "sum", "sorted", "reversed", "enumerate",
    "zip", "map", "filter", "abs", "round", "int", "float", "str", "bool",
    "list", "dict", "set", "tuple", "print", "isinstance", "type", "any", "all",
    "True", "False", "None",
]
SAFE_BUILTINS = {
    name: getattr(_builtins_module, name)
    for name in _ALLOWED_BUILTIN_NAMES
    if hasattr(_builtins_module, name)
}


def _worker(code: str, func_name: str, args: list, result_queue: "mp.Queue") -> None:
    restricted_globals = {"__builtins__": SAFE_BUILTINS}
    try:
        exec(code, restricted_globals)
        fn = restricted_globals.get(func_name)
        if fn is None:
            result_queue.put({"ok": False, "error": f"Function `{func_name}` was not defined."})
            return
        output = fn(*args)
        result_queue.put({"ok": True, "output": output})
    except Exception as exc:  # noqa: BLE001 - we want to surface any user code error
        result_queue.put({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def run_user_function(code: str, func_name: str, args: list, timeout: float = 5.0) -> dict[str, Any]:
    """Runs `func_name(*args)` from `code` in a separate process with a hard timeout.

    Returns {"ok": True, "output": ...} or {"ok": False, "error": "..."}.
    """
    ctx = mp.get_context("fork") if hasattr(mp, "get_context") else mp
    queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(code, func_name, args, queue))
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {"ok": False, "error": f"Timed out after {timeout}s (possible infinite loop)."}

    if not queue.empty():
        return queue.get()
    return {"ok": False, "error": "Process exited without a result (likely crashed)."}


def run_test_suite(code: str, func_name: str, tests: list[dict], timeout: float = 5.0) -> dict[str, Any]:
    """Runs every test case, returns a summary: passed count, total, per-test results."""
    results = []
    passed = 0
    for t in tests:
        r = run_user_function(code, func_name, t["args"], timeout=timeout)
        ok = r["ok"] and r.get("output") == t["expected"]
        if ok:
            passed += 1
        results.append({
            "args": t["args"],
            "expected": t["expected"],
            "got": r.get("output") if r["ok"] else None,
            "error": None if r["ok"] else r["error"],
            "passed": ok,
        })
    score = round(100 * passed / len(tests)) if tests else 0
    return {"passed": passed, "total": len(tests), "score": score, "results": results}
