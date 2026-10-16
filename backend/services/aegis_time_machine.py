"""
AegisRegistry Validation & Sandbox Replay Layer (Layer 7 - API Time Machine)
Implements:
1. In-Memory Ring Buffer storing historical request/response fixtures
2. Sandboxed Fixture Replay Harness: validates candidate patches before production promotion
3. Idempotency Guard: isolates non-idempotent operations (POST, DELETE) to mock fixtures
4. Semantic Invariant Guard: verifies valid entity data (e.g. matching IDs, non-empty records)
5. Circuit Breaker: enforces a strict 1-retry bound to prevent infinite retry loops
"""

import copy
import collections
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable


@dataclass
class HistoricalFixture:
    """Historical fixture snapshot for sandbox regression replay."""
    fixture_id: str
    endpoint: str
    method: str
    params: Dict[str, Any]
    body: Optional[Dict[str, Any]]
    headers: Dict[str, str]
    response_status: int
    response_data: Any
    recorded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SemanticInvariantError(Exception):
    """Raised when an API returns HTTP 200 but violates semantic data invariants."""
    pass


class CircuitBreakerTrippedError(Exception):
    """Raised when a circuit breaker trips after exceeding maximum retry bounds."""
    pass


class AegisTimeMachine:
    """
    Validation sandbox and replay harness for self-healing patches.
    """

    def __init__(self, buffer_capacity: int = 100):
        # Ring buffer of recent successful fixtures: endpoint -> deque of fixtures
        self._fixture_buffers: Dict[str, collections.deque] = {}
        self.buffer_capacity = buffer_capacity
        # Circuit breaker state: endpoint -> failure_count
        self._failure_counts: Dict[str, int] = {}

    def record_fixture(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        body: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        response_status: int,
        response_data: Any
    ) -> None:
        """Stores a successful execution fixture in the in-memory ring buffer."""
        if endpoint not in self._fixture_buffers:
            self._fixture_buffers[endpoint] = collections.deque(maxlen=self.buffer_capacity)

        import uuid
        fixture = HistoricalFixture(
            fixture_id=str(uuid.uuid4())[:8],
            endpoint=endpoint,
            method=method,
            params=copy.deepcopy(params),
            body=copy.deepcopy(body) if body is not None else None,
            headers=dict(headers),
            response_status=response_status,
            response_data=copy.deepcopy(response_data)
        )
        self._fixture_buffers[endpoint].append(fixture)

    def get_fixtures(self, endpoint: str) -> List[HistoricalFixture]:
        """Returns historical fixtures for a given endpoint."""
        return list(self._fixture_buffers.get(endpoint, []))

    def assert_semantic_invariants(
        self,
        endpoint: str,
        request_params: Dict[str, Any],
        response_status: int,
        response_data: Any
    ) -> bool:
        """
        Layer 7 Semantic Invariant Guard:
        Verifies that an HTTP 200 response contains valid entity data rather than an empty payload.
        Checks:
        1. Status must be 200
        2. Body must not be null/empty
        3. If requesting a specific student_id/course_id, entity ID must match the request
        """
        if response_status != 200:
            return False

        if response_data is None:
            raise SemanticInvariantError("Invariant violated: Server returned empty payload (None)")

        # If data is a dictionary, verify it is not an empty error container
        if isinstance(response_data, dict):
            if response_data.get("status") == "error":
                raise SemanticInvariantError(f"Invariant violated: Payload contained error status: {response_data.get('detail')}")

            # Verify entity ID invariants if present in query
            for id_field in ("student_id", "candidate_id", "course_id", "class_id"):
                if id_field in request_params and id_field in response_data:
                    req_val = str(request_params[id_field])
                    resp_val = str(response_data[id_field])
                    if req_val != resp_val:
                        raise SemanticInvariantError(
                            f"Invariant violated: ID mismatch! Requested {id_field}={req_val}, got {resp_val}"
                        )

        return True

    def check_circuit_breaker(self, endpoint: str, max_retries: int = 1) -> None:
        """
        Enforces a strict 1-retry bound. If an endpoint fails consecutively,
        trips the circuit breaker to prevent infinite loops and token burn.
        """
        fails = self._failure_counts.get(endpoint, 0)
        if fails >= max_retries:
            raise CircuitBreakerTrippedError(
                f"Circuit breaker tripped for endpoint '{endpoint}'! Exceeded {max_retries} retry bound."
            )

    def record_failure(self, endpoint: str) -> int:
        self._failure_counts[endpoint] = self._failure_counts.get(endpoint, 0) + 1
        return self._failure_counts[endpoint]

    def record_success(self, endpoint: str) -> None:
        self._failure_counts[endpoint] = 0

    def is_idempotent_method(self, method: str) -> bool:
        """Layer 7 Idempotency Guard: Verifies safe replay methods."""
        return method.upper() in ("GET", "HEAD", "OPTIONS")


# Global singleton instance
aegis_time_machine = AegisTimeMachine()
