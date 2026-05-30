import os
import socket
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class WorkerIdentity:
    """
    Identifies a worker process.

    worker_id identifies the logical worker.
    worker_run_id identifies one specific process execution.
    """

    worker_id: str
    worker_run_id: str


def build_worker_identity(worker_id: str | None = None) -> WorkerIdentity:
    """
    Build a worker identity.

    If worker_id is not provided, it is derived from hostname and process id.
    """
    resolved_worker_id = worker_id or _default_worker_id()

    return WorkerIdentity(
        worker_id=resolved_worker_id,
        worker_run_id=str(uuid4()),
    )


def _default_worker_id() -> str:
    """
    Build a default logical worker id from hostname and process id.
    """
    hostname = socket.gethostname()
    pid = os.getpid()

    return f"{hostname}:{pid}"