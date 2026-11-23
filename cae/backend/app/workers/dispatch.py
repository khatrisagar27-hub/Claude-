"""Queue a task on Celery, or run it in-process when no broker/worker is reachable.

Before this, the API swallowed the enqueue error and reported "queued" for work that never
ran (and a signature mismatch made every file import fail that way).
"""
import logging

log = logging.getLogger(__name__)


def enqueue(task, fallback, *args, background=None) -> str:
    """Returns "queued" (Celery) or "in_process" (FastAPI BackgroundTasks, or inline)."""
    try:
        conn = task.app.connection_for_write()
        conn.ensure_connection(max_retries=1, timeout=2)
        conn.release()
        task.apply_async(args=args, retry=False)
        return "queued"
    except Exception as e:  # broker down or not configured
        log.warning("Celery unavailable (%s) — running %s in-process", e, fallback.__name__)
        if background is not None:
            background.add_task(fallback, *args)
        else:
            fallback(*args)
        return "in_process"
