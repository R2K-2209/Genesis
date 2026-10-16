"""
Comprehensive Test Suite for PS 01 Scenarios
Validates 100% Zero-Touch Adaptation Rate across all synthetic mutations.
"""

import sys
import time
import threading
import uvicorn
import httpx
from mock_api import app, MutationState
from aegis.self_healing_agent import AegisSelfHealingAgent


def run_all_scenarios():
    # Start server in background thread
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1.2)

    scenarios = [
        MutationState.BASELINE,
        MutationState.RENAME,
        MutationState.TYPE_CAST,
        MutationState.NESTING,
        MutationState.HEADER,
        MutationState.COMPOUND
    ]

    print("=" * 70)
    print("  🧪 AEGISREGISTRY: COMPREHENSIVE PS 01 SCENARIO VALIDATION SUITE")
    print("=" * 70)

    results = []

    for sc in scenarios:
        # Switch mutation on mock API
        with httpx.Client(timeout=2.0) as client:
            client.post(f"http://127.0.0.1:8000/admin/mutate?scenario={sc}")

        # Run fresh agent instance
        agent = AegisSelfHealingAgent(base_url="http://127.0.0.1:8000")
        res = agent.run_task(f"Fetch student 123 under {sc}", student_id=123)

        passed = res["final_status"] in ("SUCCESS_NO_DRIFT", "SUCCESS_SELF_HEALED")
        mttr = res.get("mttr_seconds", 0.0)
        tokens = res.get("tokens_overhead", 0)

        results.append({
            "scenario": sc,
            "status": res["final_status"],
            "passed": passed,
            "mttr": mttr,
            "tokens": tokens
        })

        status_icon = "✅ PASS" if passed else "❌ FAIL"
        print(f"  [{status_icon}] Scenario '{sc:<10}': MTTR = {mttr:>5.3f}s | Tokens = {tokens:>3} | Status = {res['final_status']}")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    adaptation_rate = (passed_count / total) * 100

    print("-" * 70)
    print(f"  🎯 ZERO-TOUCH ADAPTATION RATE: {adaptation_rate:.1f}% ({passed_count}/{total} passed)")
    print(f"  ⚡ AVERAGE MTTR: {sum(r['mttr'] for r in results)/total:.3f} seconds (Target < 2.0s)")
    print("=" * 70)

    assert adaptation_rate == 100.0, "Test suite did not achieve 100% adaptation rate"


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    run_all_scenarios()
