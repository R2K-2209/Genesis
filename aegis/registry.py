"""
Immutable In-Memory MVCC Tool Registry
Provides zero-downtime hot-patching, version history, rollback, and precompiled transformation caching.
"""

import threading
import copy
from typing import Any, Callable, Dict, List, Optional, Tuple


class MVCCToolRegistry:
    """
    Multi-Version Concurrency Control (MVCC) In-Memory Tool Registry.
    Guarantees thread-safe atomic pointer swaps without application restarts.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._versions: Dict[str, Dict[str, Any]] = {}
        self._active_version: str = "v1.0"
        self._precompiled_transforms: Dict[str, Callable] = {}
        self._patch_history: List[Dict[str, Any]] = []

        # Register baseline tool definition v1.0
        self.register_initial_version(
            version="v1.0",
            schema={
                "name": "get_student_record",
                "description": "Fetch academic records for student by user_id",
                "endpoint": "/api/students",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "Student identification string"}
                    },
                    "required": ["user_id"]
                },
                "headers": {}
            }
        )

    def register_initial_version(self, version: str, schema: Dict[str, Any]):
        with self._lock:
            self._versions[version] = copy.deepcopy(schema)
            self._active_version = version

    def get_active_schema(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._versions[self._active_version])

    def get_active_version(self) -> str:
        with self._lock:
            return self._active_version

    def get_compiled_transform(self) -> Optional[Callable]:
        with self._lock:
            return self._precompiled_transforms.get(self._active_version)

    def commit_patch(
        self,
        new_version: str,
        new_schema: Dict[str, Any],
        transform_fn: Callable,
        patch_id: str,
        mutations: List[str]
    ) -> bool:
        """
        Atomically commits candidate patch to RAM and updates active version pointer.
        """
        with self._lock:
            self._versions[new_version] = copy.deepcopy(new_schema)
            self._precompiled_transforms[new_version] = transform_fn
            previous_version = self._active_version
            self._active_version = new_version

            record = {
                "patch_id": patch_id,
                "from_version": previous_version,
                "to_version": new_version,
                "mutations": mutations,
                "timestamp": "ACTIVE",
                "status": "COMMITTED"
            }
            self._patch_history.append(record)
            return True

    def rollback(self, target_version: str) -> bool:
        """
        Instant sub-millisecond rollback to previous known-good version.
        """
        with self._lock:
            if target_version in self._versions:
                self._active_version = target_version
                self._patch_history.append({
                    "action": "ROLLBACK",
                    "to_version": target_version,
                    "status": "RESTORED"
                })
                return True
            return False

    def get_patch_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._patch_history)
