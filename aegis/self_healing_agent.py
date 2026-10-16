"""
Aegis Self-Healing Agent
Orchestrates autonomous zero-downtime tool healing under runtime API schema drift.
Directly implements PS 01 end-to-end workflow under the < 2-second MTTR rule.
"""

import time
import uuid
from typing import Any, Dict, Optional
from .interceptor import AegisInterceptor
from .diagnosis import TieredDiagnosisEngine
from .provenance import FieldProvenanceGate
from .registry import MVCCToolRegistry
from .time_machine import APITimeMachine
from .ledger import RequestLedger
from .gitops import GitOpsDaemon


class AegisSelfHealingAgent:
    """
    Autonomous AI Agent with in-memory self-healing tool interface.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.interceptor = AegisInterceptor(base_url=base_url)
        self.diagnosis = TieredDiagnosisEngine()
        self.registry = MVCCToolRegistry()
        self.time_machine = APITimeMachine(base_url=base_url)
        self.ledger = RequestLedger()
        self.gitops = GitOpsDaemon()

    def run_task(self, user_prompt: str, student_id: int = 123) -> Dict[str, Any]:
        """
        Executes a user task against the registered API tool.
        Recovers autonomously if the schema has drifted.
        """
        task_start = time.perf_counter()
        telemetry = {
            "task": user_prompt,
            "target_student_id": student_id,
            "steps": [],
            "healed": False,
            "mttr_seconds": 0.0,
            "tokens_overhead": 0
        }

        # Step 1: Ingest task & inspect active tool definition
        schema = self.registry.get_active_schema()
        telemetry["initial_schema_version"] = self.registry.get_active_version()

        # Build initial payload based on active tool definition
        active_transform = self.registry.get_compiled_transform()
        if active_transform:
            payload, headers = active_transform({"user_id": str(student_id)}, {})
            telemetry["steps"].append(f"Used precompiled lambda transform in RAM for {self.registry.get_active_version()}")
        else:
            payload = {"user_id": str(student_id)}
            headers = {}
            telemetry["steps"].append(f"Dispatched tool '{schema['name']}' with v1.0 payload: {payload}")

        # Step 2: Dispatch through runtime interceptor
        dispatch_result = self.interceptor.execute_with_interception(
            endpoint=schema["endpoint"],
            method=schema["method"],
            payload=payload,
            headers=headers,
            expected_entity_id=student_id
        )

        # Path A: Request succeeded without drift
        if not dispatch_result.get("drift_detected") and dispatch_result.get("status_code") == 200:
            elapsed = time.perf_counter() - task_start
            telemetry["steps"].append("Request completed successfully on first attempt.")
            telemetry["final_status"] = "SUCCESS_NO_DRIFT"
            telemetry["total_time_seconds"] = round(elapsed, 3)
            telemetry["data"] = dispatch_result.get("data")
            return telemetry

        # Path B: Schema Drift Detected (HTTP 422/400) -> Trigger Self-Healing Zone
        drift_start = time.perf_counter()
        telemetry["healed"] = True
        telemetry["steps"].append(
            f"Caught HTTP {dispatch_result.get('status_code')} drift error: {dispatch_result.get('error_data')}"
        )

        # 1. Acquire Single-Flight Mutex (Thundering Herd shield)
        self.interceptor.acquire_single_flight_lock()
        telemetry["steps"].append("Single-Flight Mutex acquired: concurrent requests paused.")

        try:
            # 2. Tiered Diagnosis Engine (Fast-Path AST < 15ms)
            diff = self.diagnosis.diagnose_and_compile(
                original_payload=payload,
                original_headers=headers,
                error_response=dispatch_result.get("error_data")
            )
            telemetry["diagnosis_tier"] = diff.get("diagnosis_tier")
            telemetry["diagnosis_latency_ms"] = diff.get("latency_ms")
            telemetry["tokens_overhead"] = diff.get("tokens_used", 0)
            telemetry["mutations_resolved"] = diff.get("mutations_detected")
            telemetry["steps"].append(
                f"Diagnosed diff via {diff.get('diagnosis_tier')} in {diff.get('latency_ms')}ms (Tokens: {diff.get('tokens_used')})"
            )

            # 3. Field Provenance & Anti-Hallucination Gate
            transform_fn = diff["transform_fn"]
            new_payload, new_headers = transform_fn(payload, headers)
            is_safe, reasons = FieldProvenanceGate.verify_patch_provenance(
                user_prompt=user_prompt,
                original_payload=payload,
                transformed_payload=new_payload,
                injected_headers=diff.get("required_headers", {})
            )
            if not is_safe:
                telemetry["final_status"] = "REJECTED_HALLUCINATION_RISK"
                telemetry["rejection_reasons"] = reasons
                return telemetry

            telemetry["steps"].append("Provenance Gate passed: 0.0% hallucinated business fields.")

            # 4. API Time Machine: Sandboxed Regression Replay
            replay_ok, replay_logs = self.time_machine.run_regression_replay()
            if not replay_ok:
                telemetry["final_status"] = "ROLLBACK_REGRESSION_DETECTED"
                return telemetry

            telemetry["steps"].append("API Time Machine: Sandboxed regression fixtures PASSED.")

            # 5. In-Memory Atomic Hot-Patch (MVCC)
            patch_id = f"PATCH-STUDENTS-{uuid.uuid4().hex[:6].upper()}"
            new_version = "v1.1"
            self.registry.commit_patch(
                new_version=new_version,
                new_schema=diff["candidate_schema"],
                transform_fn=transform_fn,
                patch_id=patch_id,
                mutations=diff.get("mutations_detected")
            )
            telemetry["steps"].append(f"Atomically committed hot-patch to RAM: v1.0 -> {new_version} ({patch_id})")

        finally:
            self.interceptor.release_single_flight_lock()

        # Step 3: Resumed Retry Dispatch with Transformed Payload
        telemetry["steps"].append(f"Retrying request with transformed payload: {new_payload} and headers: {new_headers}")
        retry_result = self.interceptor.execute_with_interception(
            endpoint=schema["endpoint"],
            method=schema["method"],
            payload=new_payload,
            headers=new_headers,
            expected_entity_id=student_id
        )

        recovery_elapsed = time.perf_counter() - drift_start
        total_elapsed = time.perf_counter() - task_start

        telemetry["mttr_seconds"] = round(recovery_elapsed, 3)
        telemetry["total_time_seconds"] = round(total_elapsed, 3)

        if retry_result.get("status_code") == 200:
            telemetry["final_status"] = "SUCCESS_SELF_HEALED"
            telemetry["data"] = retry_result.get("data")
            telemetry["steps"].append(f"Request completed with HTTP 200 OK in {round(recovery_elapsed, 3)}s MTTR!")

            # Step 4: Record in Request Ledger
            trace_id = self.ledger.record_transaction(
                patch_id=patch_id,
                tool_name=schema["name"],
                original_payload=payload,
                transformed_payload=new_payload,
                response_data=retry_result.get("data"),
                latency_ms=recovery_elapsed * 1000
            )
            telemetry["ledger_trace_id"] = trace_id
            undo_sql, is_safe_sql, _ = self.ledger.generate_compensating_sql(patch_id)
            telemetry["compensating_sql"] = undo_sql

            # Step 5: Asynchronous GitOps Auto-PR Daemon
            pr = self.gitops.trigger_auto_pr(
                tool_name=schema["name"],
                patch_id=patch_id,
                old_version="v1.0",
                new_version=new_version,
                mutations=diff.get("mutations_detected"),
                candidate_schema=diff.get("candidate_schema")
            )
            telemetry["gitops_pr_url"] = pr["url"]
            telemetry["gitops_pr_title"] = pr["title"]
            telemetry["steps"].append(f"Opened automated GitHub PR: {pr['title']}")

        else:
            telemetry["final_status"] = "RETRY_FAILED_CIRCUIT_BREAKER"
            self.registry.rollback("v1.0")
            telemetry["steps"].append("Resumed retry failed; Circuit Breaker triggered rollback to v1.0.")

        return telemetry
