"""
AegisRegistry MVCC Registry & In-Memory Hot-Patching Layer (Layer 6)
Implements:
1. Immutable SchemaSnapshot models with embedded transform lambdas and cryptographic fingerprints
2. Atomic Pointer Swapping (MVCC) without mutex locks on read paths
3. Dynamic Lambda compilation for 0.0001s (<0.1ms) hot-path transformation execution
4. Full version tracking (v1.0 -> v1.1 -> v1.2) with parent pointer ancestry
"""

import time
import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Tuple, List
from backend.services.aegis_diagnoser import SchemaDiff


@dataclass(frozen=True)
class SchemaSnapshot:
    """
    Immutable state model for an API endpoint contract version (Layer 6).
    Enforces atomic pointer swapping and thread-safe lock-free reads.
    """
    version: str                                  # e.g., "v1.1"
    endpoint: str                                 # e.g., "/api/v1/students/{id}/degree-audit"
    tool_name: str = ""                           # e.g., "complex-graduation-audit"
    diff: Optional[SchemaDiff] = None             # Diagnosed AST diff
    json_schema: Dict[str, Any] = field(default_factory=dict) # JSON Schema definition
    transform_lambda: Optional[Callable] = None   # Precompiled Python transformation callable
    parent_version: Optional[str] = None          # e.g., "v1.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    applied_count: int = 0
    fingerprint: str = ""                         # Cryptographic SHA-256 fingerprint


class AegisMVCCRegistry:
    """
    Manages in-memory hot-patch snapshots and performs atomic pointer swapping (MVCC).
    Guarantees thread-safe, lock-free reads across concurrent requests.
    """

    def __init__(self):
        # endpoint/tool_name -> active SchemaSnapshot reference (atomically swapped)
        self._active_snapshots: Dict[str, SchemaSnapshot] = {}
        # Historical snapshot ledger: endpoint -> List[SchemaSnapshot]
        self._snapshot_history: Dict[str, List[SchemaSnapshot]] = {}

    def get_snapshot(self, endpoint: str) -> SchemaSnapshot:
        """
        Lock-free read: returns the current immutable SchemaSnapshot reference.
        Any running coroutine keeps this exact reference until completion,
        even if another coroutine swaps the pointer concurrently.
        """
        snapshot = self._active_snapshots.get(endpoint)
        if snapshot is None:
            snapshot = SchemaSnapshot(
                version="v1.0",
                endpoint=endpoint,
                tool_name=endpoint,
                fingerprint=self._compute_fingerprint("v1.0", endpoint, None)
            )
            self._active_snapshots[endpoint] = snapshot
        return snapshot

    def has_hot_patch(self, endpoint: str) -> bool:
        snapshot = self._active_snapshots.get(endpoint)
        return snapshot is not None and snapshot.version != "v1.0" and snapshot.transform_lambda is not None

    def apply_hot_patch(
        self,
        endpoint: str,
        params: Dict[str, Any],
        body: Optional[Dict[str, Any]],
        headers: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Dict[str, str], Optional[str]]:
        """
        Executes precompiled hot-patch transformation in memory (<0.1ms).
        Returns: (healed_params, healed_body, healed_headers, redirected_path)
        """
        snapshot = self.get_snapshot(endpoint)
        if snapshot.transform_lambda is not None:
            return snapshot.transform_lambda(params, body, headers)
        return params, body, headers, None

    def compile_and_register_patch(
        self,
        endpoint: str,
        diff: SchemaDiff,
        tool_name: Optional[str] = None
    ) -> SchemaSnapshot:
        """
        Compiles a diagnosed SchemaDiff into an in-memory transformation lambda
        and performs an ATOMIC POINTER SWAP to the new SchemaSnapshot.
        Tool definitions in Python are never mutated in place.
        """
        current_snapshot = self.get_snapshot(endpoint)
        next_ver = self._increment_version(current_snapshot.version)
        name = tool_name or current_snapshot.tool_name or endpoint

        # Build dynamic transformer callable: (params, body, headers) -> (healed_params, healed_body, healed_headers, redirected_path)
        def compiled_transformer(
            p: Dict[str, Any],
            b: Optional[Dict[str, Any]],
            h: Dict[str, str]
        ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Dict[str, str], Optional[str]]:
            healed_params = copy.deepcopy(p)
            healed_body = copy.deepcopy(b) if b is not None else None
            healed_headers = dict(h)
            redirected_path = diff.route_redirect

            # 1. Apply field renames
            for old_key, new_key in diff.field_renames.items():
                if old_key.startswith("_inject_"):
                    # Missing parameter injection
                    real_key = old_key.replace("_inject_", "")
                    if real_key not in healed_params:
                        healed_params[real_key] = "all"
                elif old_key in healed_params:
                    val = healed_params.pop(old_key)
                    healed_params[new_key] = val
                elif healed_body and old_key in healed_body:
                    val = healed_body.pop(old_key)
                    healed_body[new_key] = val

            # 2. Apply type casts
            for key, target_type in diff.type_casts.items():
                if key in healed_params:
                    val = healed_params[key]
                    try:
                        if target_type in ("int", "integer"):
                            healed_params[key] = int(val)
                        elif target_type in ("str", "string"):
                            healed_params[key] = str(val)
                        elif target_type in ("float", "real"):
                            healed_params[key] = float(val)
                    except (ValueError, TypeError):
                        pass

            # 3. Apply nested wrapping
            for child_key, wrapper in diff.nested_wraps.items():
                if child_key in healed_params:
                    val = healed_params.pop(child_key)
                    if wrapper not in healed_params:
                        healed_params[wrapper] = {}
                    if isinstance(healed_params[wrapper], dict):
                        healed_params[wrapper][child_key] = val

            # 4. Inject required headers
            for h_key, h_val in diff.injected_headers.items():
                healed_headers[h_key] = h_val

            return healed_params, healed_body, healed_headers, redirected_path

        fingerprint = self._compute_fingerprint(next_ver, endpoint, diff)

        # Create new immutable snapshot
        new_snapshot = SchemaSnapshot(
            version=next_ver,
            endpoint=endpoint,
            tool_name=name,
            diff=diff,
            json_schema={
                "endpoint": endpoint,
                "version": next_ver,
                "renames": diff.field_renames,
                "type_casts": diff.type_casts,
                "headers": diff.injected_headers
            },
            transform_lambda=compiled_transformer,
            parent_version=current_snapshot.version,
            applied_count=current_snapshot.applied_count + 1,
            fingerprint=fingerprint
        )

        # Record history
        if endpoint not in self._snapshot_history:
            self._snapshot_history[endpoint] = [current_snapshot]
        self._snapshot_history[endpoint].append(new_snapshot)

        # ATOMIC POINTER SWAP (MVCC):
        # Replace the pointer in the dictionary. Any ongoing read coroutines referencing
        # current_snapshot will safely complete on current_snapshot without locking.
        # All subsequent calls immediately receive new_snapshot.
        self._active_snapshots[endpoint] = new_snapshot
        return new_snapshot

    def get_history(self, endpoint: str) -> List[SchemaSnapshot]:
        """Returns the immutable version history of an endpoint."""
        return list(self._snapshot_history.get(endpoint, [self.get_snapshot(endpoint)]))

    def reset_endpoint(self, endpoint: str) -> None:
        """Resets an endpoint back to clean v1.0 baseline."""
        baseline = SchemaSnapshot(
            version="v1.0",
            endpoint=endpoint,
            tool_name=endpoint,
            fingerprint=self._compute_fingerprint("v1.0", endpoint, None)
        )
        self._active_snapshots[endpoint] = baseline

    def reset_all(self) -> None:
        """Resets all snapshots back to clean baseline."""
        self._active_snapshots.clear()
        self._snapshot_history.clear()

    def _increment_version(self, current_ver: str) -> str:
        try:
            if current_ver.startswith("v"):
                parts = current_ver[1:].split(".")
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
                return f"v{major}.{minor + 1}"
        except Exception:
            pass
        return "v1.1"

    def _compute_fingerprint(self, version: str, endpoint: str, diff: Optional[SchemaDiff]) -> str:
        content = f"{version}:{endpoint}:{diff.field_renames if diff else ''}:{diff.type_casts if diff else ''}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


# Global singleton instance
aegis_mvcc_registry = AegisMVCCRegistry()
