"""
AegisRegistry Interception & Concurrency Guard Layer (Layer 3)
Wraps downstream API dispatches with:
1. In-Memory Hot-Patch Execution (<0.1ms for cached schemas)
2. Single-Flight Concurrency Mutex (Promise Sharing across parallel requests)
3. Deterministic AST Diagnosis & Provenance Assertion
4. Seamless Replay & Self-Healing Telemetry Synthesis
5. Circuit Breaker (Strict 1-retry bound)
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, Tuple, Coroutine

from backend.services.aegis_diagnoser import aegis_diagnoser, SchemaDiff
from backend.services.aegis_provenance import aegis_provenance_gate, ProvenanceResult
from backend.services.aegis_mvcc import aegis_mvcc_registry, SchemaSnapshot
from backend.services.aegis_ledger import aegis_request_ledger


@dataclass
class AegisExecutionResult:
    status_code: int
    data: Any
    healed: bool = False
    original_version: str = "v1.0"
    active_version: str = "v1.0"
    diff: Optional[SchemaDiff] = None
    provenance: Optional[ProvenanceResult] = None
    diagnosis_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    error: Optional[str] = None
    circuit_breaker_tripped: bool = False


class AegisInterceptor:
    """
    Autonomous tool interceptor and self-healing runtime controller.
    """

    def __init__(self):
        # Single-flight concurrency shield: endpoint -> asyncio.Lock
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, endpoint: str) -> asyncio.Lock:
        if endpoint not in self._locks:
            self._locks[endpoint] = asyncio.Lock()
        return self._locks[endpoint]

    async def execute_with_self_healing(
        self,
        endpoint: str,
        params: Dict[str, Any],
        body: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        dispatch_fn: Callable[[str, Dict[str, Any], Optional[Dict[str, Any]], Dict[str, str]], Coroutine[Any, Any, Tuple[int, Any]]],
        user_prompt: str = ""
    ) -> AegisExecutionResult:
        start_time = time.perf_counter()

        current_snapshot = aegis_mvcc_registry.get_snapshot(endpoint)
        orig_version = current_snapshot.version

        # Step 1: Pre-apply in-memory hot-patch if already compiled
        active_params, active_body, active_headers, redirected_path = aegis_mvcc_registry.apply_hot_patch(
            endpoint=endpoint,
            params=params,
            body=body,
            headers=headers
        )
        active_endpoint = redirected_path if redirected_path else endpoint

        # Step 2: Execute initial dispatch
        status_code, response_data = await dispatch_fn(active_endpoint, active_params, active_body, active_headers)

        # If HTTP 200, return immediately
        if status_code == 200:
            total_latency = round((time.perf_counter() - start_time) * 1000, 2)
            is_healed = orig_version != "v1.0" or current_snapshot.diff is not None
            return AegisExecutionResult(
                status_code=200,
                data=response_data,
                healed=is_healed,
                original_version=orig_version,
                active_version=current_snapshot.version,
                diff=current_snapshot.diff,
                total_latency_ms=total_latency
            )

        # Step 3: Drift Detected! Engage Interception & Single-Flight Mutex
        if status_code in (400, 404, 422):
            lock = self._get_lock(endpoint)
            async with lock:
                # Re-check if another concurrent coroutine already compiled a patch while we waited
                recheck_snapshot = aegis_mvcc_registry.get_snapshot(endpoint)
                if recheck_snapshot.version != orig_version:
                    # Retry with newly compiled patch
                    p_healed, b_healed, h_healed, r_path = aegis_mvcc_registry.apply_hot_patch(
                        endpoint=endpoint,
                        params=params,
                        body=body,
                        headers=headers
                    )
                    s_code, r_data = await dispatch_fn(r_path or endpoint, p_healed, b_healed, h_healed)
                    if s_code == 200:
                        total_lat = round((time.perf_counter() - start_time) * 1000, 2)
                        return AegisExecutionResult(
                            status_code=200,
                            data=r_data,
                            healed=True,
                            original_version=orig_version,
                            active_version=recheck_snapshot.version,
                            diff=recheck_snapshot.diff,
                            total_latency_ms=total_lat
                        )

                # Tier 1 & Tier 2: Diagnose Schema Drift
                diag_start = time.perf_counter()
                diff = aegis_diagnoser.diagnose(
                    endpoint=endpoint,
                    original_params=params,
                    original_body=body,
                    original_headers=headers,
                    status_code=status_code,
                    error_payload=response_data
                )
                diag_latency = round((time.perf_counter() - diag_start) * 1000, 2)

                # Step 4: Provenance Assertion (Zero-Hallucination Gate)
                provenance = aegis_provenance_gate.verify_provenance(
                    healed_params={**params, **diff.field_renames},
                    original_params=params,
                    user_prompt=user_prompt
                )

                if not provenance.is_valid:
                    total_lat = round((time.perf_counter() - start_time) * 1000, 2)
                    return AegisExecutionResult(
                        status_code=status_code,
                        data=response_data,
                        healed=False,
                        error=f"Aegis Provenance Gate Blocked Healing: {', '.join(provenance.violations)}",
                        provenance=provenance,
                        diagnosis_latency_ms=diag_latency,
                        total_latency_ms=total_lat
                    )

                # Step 5: Compile & Atomic Pointer Swap (MVCC)
                new_snapshot = aegis_mvcc_registry.compile_and_register_patch(endpoint=endpoint, diff=diff)

                # Step 6: Sandboxed Replay with Healed Payload
                healed_params, healed_body, healed_headers, redirected_path = aegis_mvcc_registry.apply_hot_patch(
                    endpoint=endpoint,
                    params=params,
                    body=body,
                    headers=headers
                )
                replay_endpoint = redirected_path if redirected_path else endpoint

                replay_status, replay_data = await dispatch_fn(
                    replay_endpoint,
                    healed_params,
                    healed_body,
                    healed_headers
                )

                total_latency = round((time.perf_counter() - start_time) * 1000, 2)

                if replay_status == 200:
                    # Record in Request Ledger
                    aegis_request_ledger.record_healing(
                        endpoint=endpoint,
                        drift_type=diff.drift_type,
                        original_payload={"params": params, "body": body, "headers": headers},
                        healed_payload={"params": healed_params, "body": healed_body, "headers": healed_headers},
                        status_code_before=status_code,
                        status_code_after=200,
                        diagnosis_latency_ms=diag_latency,
                        total_latency_ms=total_latency,
                        provenance_verified=True,
                        explanation=diff.explanation
                    )

                    return AegisExecutionResult(
                        status_code=200,
                        data=replay_data,
                        healed=True,
                        original_version=orig_version,
                        active_version=new_snapshot.version,
                        diff=diff,
                        provenance=provenance,
                        diagnosis_latency_ms=diag_latency,
                        total_latency_ms=total_latency
                    )
                else:
                    # Circuit breaker triggered (strict 1-retry bound)
                    return AegisExecutionResult(
                        status_code=replay_status,
                        data=replay_data,
                        healed=False,
                        original_version=orig_version,
                        active_version=new_snapshot.version,
                        diff=diff,
                        provenance=provenance,
                        diagnosis_latency_ms=diag_latency,
                        total_latency_ms=total_latency,
                        error=f"Circuit Breaker: Healed request failed with HTTP {replay_status}",
                        circuit_breaker_tripped=True
                    )

        # Fallthrough for other status codes (e.g. 500 server errors)
        total_latency = round((time.perf_counter() - start_time) * 1000, 2)
        return AegisExecutionResult(
            status_code=status_code,
            data=response_data,
            healed=False,
            total_latency_ms=total_latency,
            error=str(response_data)
        )


# Global singleton instance
aegis_interceptor = AegisInterceptor()
