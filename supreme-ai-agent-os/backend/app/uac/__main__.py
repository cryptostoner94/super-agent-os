"""
UAC CLI entry point.

Usage
-----
    python -m uac status              # print one-shot status
    python -m uac run --pulses 5      # run heartbeat loop for N pulses
    python -m uac dashboard           # console dashboard
    python -m uac web [--port 8765]   # launch web dashboard
    python -m uac skill <name> ...    # run a single skill (key=value args)
    python -m uac plan "<goal>"       # synthesize and execute a plan
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List

from .runtime import Runtime
from .dashboard import ConsoleDashboard, WebDashboard


def _parse_kv(args: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for a in args:
        if "=" not in a:
            continue
        k, _, v = a.partition("=")
        # try to coerce JSON value, else keep string
        try:
            out[k] = json.loads(v)
        except Exception:
            out[k] = v
    return out


async def _cmd_run(rt: Runtime, pulses: int) -> None:
    await rt.run_forever(max_pulses=pulses if pulses > 0 else None)


async def _cmd_dashboard(rt: Runtime, iterations: int) -> None:
    dash = ConsoleDashboard(rt)
    pulse_task = asyncio.create_task(rt.run_forever(max_pulses=iterations or None))
    render_task = asyncio.create_task(dash.run(iterations=iterations or None))
    try:
        await asyncio.gather(pulse_task, render_task)
    except KeyboardInterrupt:
        rt.stop(); dash.stop()


def _cmd_web(rt: Runtime, host: str, port: int, seconds: int) -> None:
    web = WebDashboard(rt, host=host, port=port)
    url = web.start()
    print(f"UAC web dashboard up at {url}")
    # also run the heartbeat in the background so /status reflects live data
    loop = asyncio.new_event_loop()
    def _runner() -> None:
        loop.run_until_complete(rt.run_forever(
            max_pulses=(seconds // 2) if seconds > 0 else None))
    import threading
    t = threading.Thread(target=_runner, daemon=True); t.start()
    try:
        import time
        if seconds > 0:
            time.sleep(seconds)
        else:
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        rt.stop(); web.stop()


async def _cmd_skill(rt: Runtime, name: str, ctx: Dict[str, Any]) -> None:
    sr = await rt.step_once(name, ctx)
    print(json.dumps({
        "skill": sr.skill,
        "passed": sr.verdict.passed,
        "score": sr.verdict.score,
        "result": sr.result.to_work_unit(),
    }, indent=2, default=str))


async def _cmd_plan(rt: Runtime, goal: str) -> None:
    plan_sr = await rt.step_once("plan_synthesis", {"goal": goal})
    plan = plan_sr.result.outputs.get("steps", [])
    print(f"plan ({len(plan)} step(s)) for goal: {goal!r}")
    results = await rt.run_plan(plan)
    out = []
    for r in results:
        out.append({
            "skill": r.skill,
            "passed": r.verdict.passed,
            "score": round(r.verdict.score, 3),
            "status": r.result.status,
        })
    print(json.dumps(out, indent=2))


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="uac", description="Ultimate Autonomous Core")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    p_run = sub.add_parser("run"); p_run.add_argument("--pulses", type=int, default=0)
    p_d = sub.add_parser("dashboard"); p_d.add_argument("--iterations", type=int, default=0)
    p_w = sub.add_parser("web")
    p_w.add_argument("--host", default="127.0.0.1")
    p_w.add_argument("--port", type=int, default=8765)
    p_w.add_argument("--seconds", type=int, default=0,
                     help="run for N seconds then exit (0 = forever)")
    p_s = sub.add_parser("skill"); p_s.add_argument("name")
    p_s.add_argument("kv", nargs="*", help="key=value pairs (JSON-safe)")
    p_pl = sub.add_parser("plan"); p_pl.add_argument("goal")

    args = p.parse_args(argv)
    rt = Runtime()

    if args.cmd == "status":
        print(json.dumps(rt.status(), indent=2, default=str)); return 0
    if args.cmd == "run":
        asyncio.run(_cmd_run(rt, args.pulses)); return 0
    if args.cmd == "dashboard":
        asyncio.run(_cmd_dashboard(rt, args.iterations)); return 0
    if args.cmd == "web":
        _cmd_web(rt, args.host, args.port, args.seconds); return 0
    if args.cmd == "skill":
        asyncio.run(_cmd_skill(rt, args.name, _parse_kv(args.kv))); return 0
    if args.cmd == "plan":
        asyncio.run(_cmd_plan(rt, args.goal)); return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
