import logging

from pyxis.aws.config import ConfigFactory

from apus_monitoring import channels, loader
from apus_monitoring.executor import Executor

config = ConfigFactory.default_application()


def main():
    """Entrypoint for the monitoring application."""

    monitors = loader.load_monitors(config)

    if not monitors:
        logging.info('no monitors found, exiting')
        return

    suppressed_errors = []
    executor = Executor(max_workers=min(10, len(monitors)))
    for monitor in monitors:
        executor.submit(monitor)

    for future, monitor in executor.futures():
        try:
            alerts = future.result()
        except Exception as e:
            logging.exception('monitor %s failed', monitor.metadata.name)
            suppressed_errors.append(e)
            continue

        if not alerts:
            logging.info('no alerts for monitor %s, skipping', monitor.metadata.name)
            continue

        for i, channel in enumerate(channels.dispatch(monitor)):
            try:
                channel.send(alerts)
            except Exception as e:  # noqa: PERF203
                logging.exception('%s channels[%s] failed for monitor %s', channel.type, i, monitor.metadata.name)
                suppressed_errors.append(e)

    if suppressed_errors:
        raise RuntimeError('one or more errors occurred during execution', suppressed_errors)


if __name__ == '__main__':
    main()
