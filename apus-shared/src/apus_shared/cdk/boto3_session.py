import threading

import boto3

__session = None
__lock = threading.Lock()


def Session(*args, **kwargs) -> boto3.Session:  # noqa: N802
    global __session  # noqa: PLW0603
    if __session is None:
        with __lock:
            if __session is None:
                __session = boto3.Session(*args, **kwargs)
    return __session


def __getattr__(name):
    if __session is None:
        raise RuntimeError('Session has not been initialized yet. Call Session() first.')
    return getattr(__session, name)
