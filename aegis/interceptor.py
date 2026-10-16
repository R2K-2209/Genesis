"""
Runtime Transport Interceptor & Concurrency Guard
Intercepts 4xx/drift, enforces Single-Flight Mutex concurrency locking,
and validates post-execution semantic invariants.
"""

import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple
import httpx


class AegisInterceptor:
    """
    Wraps outbound HTTP tool dispatches with concurrency protection,
    runtime error interception, and semantic invariant validation.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self._mutex = threading.Lock()
        self._is_healing = False

    def execute_with_interception(
        self,
        endpoint: str,
        method: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        expected_entity_id: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes HTTP dispatch, catching 4xx drift errors before agent crash.
        """
        url = f"{self.base_url}{endpoint}"
        start_time = time.perf_counter()

        try:
            with httpx.Client(timeout=3.0) as client:
                if method.upper() == "POST":
                    response = client.post(url, json=payload, headers=headers)
                else:
                    response = client.get(url, headers=headers)

                elapsed_ms = (time.perf_counter() - start_time) * 1000

                # 1. Catch 422 or 400 runtime schema drift
                if response.status_code in (422, 400):
                    try:
                        err_json = response.json()
                    except Exception:
                        err_json = {"detail": response.text}

                    return {
                        "drift_detected": True,
                        "status_code": response.status_code,
                        "error_data": err_json,
                        "latency_ms": elapsed_ms
                    }

                # 2. Check Semantic Invariant on 200 OK (Catch silent drift)
                elif response.status_code == 200:
                    resp_json = response.json()
                    is_valid, invariant_err = self.verify_semantic_invariant(resp_json, expected_entity_id)
                    if not is_valid:
                        return {
                            "drift_detected": True,
                            "silent_drift": True,
                            "status_code": 200,
                            "error_data": {"detail": invariant_err},
                            "latency_ms": elapsed_ms
                        }

                    return {
                        "drift_detected": False,
                        "status_code": 200,
                        "data": resp_json,
                        "latency_ms": elapsed_ms
                    }

                else:
                    return {
                        "drift_detected": False,
                        "status_code": response.status_code,
                        "error_data": response.text,
                        "latency_ms": elapsed_ms
                    }

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "drift_detected": False,
                "network_error": str(e),
                "status_code": 500,
                "latency_ms": elapsed_ms
            }

    @staticmethod
    def verify_semantic_invariant(
        response_json: Dict[str, Any],
        expected_entity_id: Optional[Any]
    ) -> Tuple[bool, str]:
        """
        Validates that the returned data actually satisfies task requirements.
        Prevents returning empty data or wrong entities on HTTP 200.
        """
        data = response_json.get("data")
        if not data:
            return False, "Semantic Violation: API returned HTTP 200 but response data payload is empty."

        if expected_entity_id is not None:
            returned_id = data.get("id") or data.get("student_id")
            if returned_id is not None and str(returned_id) != str(expected_entity_id):
                return False, f"Semantic Violation: Requested ID {expected_entity_id}, but API returned ID {returned_id}."

        return True, "Semantic invariants satisfied."

    def acquire_single_flight_lock(self) -> bool:
        """
        Locks the healing gate to prevent Thundering Herd concurrency spikes.
        """
        return self._mutex.acquire(blocking=False)

    def release_single_flight_lock(self):
        if self._mutex.locked():
            self._mutex.release()
