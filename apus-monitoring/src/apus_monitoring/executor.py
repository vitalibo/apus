from collections.abc import Generator
from concurrent.futures import Future, as_completed
from concurrent.futures.thread import ThreadPoolExecutor

from apus_shared.models import Resource
from jinja2 import Template
from sqlalchemy import text

from apus_monitoring.models import BusinessMonitor


class Executor:
    """Executor for running monitors in parallel using ThreadPoolExecutor."""

    def __init__(self, max_workers):
        self.__thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.__futures = {}

    def submit(self, resource: Resource[BusinessMonitor]) -> Future:
        """Submit a monitor for execution."""

        future = self.__thread_pool.submit(self.execute, resource.spec)
        self.__futures[future] = resource
        return future

    def futures(self) -> Generator[tuple[Future, Resource[BusinessMonitor]]]:
        """Yields futures as they complete, along with their corresponding resources."""

        try:
            for future in as_completed(self.__futures):
                yield future, self.__futures[future]

        finally:
            self.__thread_pool.shutdown(wait=False)

    @staticmethod
    def execute(monitor: BusinessMonitor):
        """Execute a single monitor."""

        engine = monitor.connection.create_engine()
        query = Template(monitor.query_template).render()

        with engine.connect() as conn:
            result = conn.execute(text(query))
            return [dict(row._mapping) for row in result.fetchall()]  # noqa: SLF001
