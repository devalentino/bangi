import atexit
import logging
from collections import defaultdict
from collections.abc import Callable
from queue import Queue
from threading import Event, Lock, Thread
from typing import Annotated, TypeAlias

from peewee import MySQLDatabase
from wireup import Inject, injectable

from src.core.db import ReconnectPooledMySQLDatabase

logger = logging.getLogger(__name__)

Worker: TypeAlias = Callable[['WorkerContext'], None]
_REGISTERED_WORKERS: dict[str, list[Worker]] = defaultdict(list)


def get_worker_name(worker: Worker) -> str:
    return f'{worker.__module__}.{worker.__qualname__}'


def register_worker(worker: Worker) -> Worker:
    worker_name = get_worker_name(worker)
    workers = _REGISTERED_WORKERS[worker_name]
    if worker not in workers:
        workers.append(worker)
    return worker


@injectable(lifetime='singleton')
class WorkerContext:
    def __init__(
        self,
        host: Annotated[str, Inject(config='MARIADB_HOST')],
        port: Annotated[int, Inject(config='MARIADB_PORT')],
        username: Annotated[str, Inject(config='MARIADB_USER')],
        password: Annotated[str, Inject(config='MARIADB_PASSWORD')],
        db_name: Annotated[str, Inject(config='MARIADB_DATABASE')],
    ):
        self.database: MySQLDatabase = ReconnectPooledMySQLDatabase(
            db_name,
            user=username,
            password=password,
            host=host,
            port=port,
        )
        self._queues: dict[str, Queue[dict[str, object]]] = {}
        self._state: dict[str, dict[str, object]] = {}
        self._queues_lock = Lock()
        self._state_lock = Lock()

    def get_queue(self, worker: Worker) -> Queue[dict[str, object]]:
        worker_name = get_worker_name(worker)
        queue = self._queues.get(worker_name)
        if queue is None:
            with self._queues_lock:
                queue = self._queues.get(worker_name)
                if queue is None:
                    queue = Queue()
                    self._queues[worker_name] = queue
        return queue

    def get_state(self, worker: Worker) -> dict[str, object]:
        worker_name = get_worker_name(worker)
        state = self._state.get(worker_name)
        if state is None:
            with self._state_lock:
                state = self._state.get(worker_name)
                if state is None:
                    state = {}
                    self._state[worker_name] = state
        return state

    def close(self) -> None:
        if not self.database.is_closed():
            self.database.close()


@injectable(lifetime='singleton')
class WorkerSupervisor:
    def __init__(
        self,
        context: WorkerContext,
        poll_seconds: Annotated[float, Inject(config='BACKGROUND_SUPERVISOR_POLL_SECONDS')],
    ):
        self.context = context
        self.poll_seconds = poll_seconds
        self._workers = _REGISTERED_WORKERS
        self._stop_event = Event()
        self._thread = Thread(target=self._run, name='worker-supervisor', daemon=True)
        self._thread.start()
        atexit.register(self.stop)

    def enqueue(self, worker: Worker, payload: dict[str, object]) -> None:
        self.context.get_queue(worker).put(payload)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1)
        self.context.close()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._stop_event.wait(self.poll_seconds)
            if self._stop_event.is_set():
                break

            for worker_name, workers in self._workers.items():
                for worker in workers:
                    try:
                        worker(self.context)
                    except Exception:
                        logger.exception(
                            'Failed to execute worker',
                            extra={'worker_name': worker_name, 'worker': getattr(worker, '__name__', repr(worker))},
                        )
