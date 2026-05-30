import argparse

from app.observability.logging import configure_logging
from app.worker.config import build_worker_config
from app.worker.worker import Worker
from app.worker.worker_identity import build_worker_identity


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run a background job worker.",
    )

    parser.add_argument(
        "--queue",
        default="default",
        help="Queue name to process.",
    )

    parser.add_argument(
        "--worker-id",
        default=None,
        help="Optional logical worker id.",
    )

    return parser.parse_args()


def main() -> None:
    """
    Start the worker process.
    """
    configure_logging()

    args = parse_args()

    config = build_worker_config(queue_name=args.queue)
    identity = build_worker_identity(worker_id=args.worker_id)

    worker = Worker(
        config=config,
        identity=identity,
    )

    worker.run_forever()


if __name__ == "__main__":
    main()