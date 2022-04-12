#!/usr/bin/env python3

import json
import logging
from functools import wraps
from time import sleep
from typing import Any, Callable, Dict, List, Optional, NamedTuple, Tuple, Union

from redis import Redis
from redis.exceptions import LockError, LockNotOwnedError
from redis.lock import Lock


JSONOrderedDict = List[Tuple[str, Any]]
JSONValue = Union[Dict, List, str, int, float, bool, None]


class TaskStatus(NamedTuple):
    done: bool
    value: Optional[JSONValue]
    load: int


def format_key(key_type: str, key_params: Dict[str, Any]) -> str:
    key_params_list = sorted(key_params.items())
    return json.dumps([key_type, key_params_list])


def parse_key(key: str) -> Tuple[str, Dict[str, Any]]:
    (key_type, key_params_list) = json.loads(key)
    return (key_type, dict(key_params_list))


def _star_wrap(handler: Callable[..., JSONValue]) -> Callable[[Dict[str, Any]], JSONValue]:
    @wraps(handler)
    def h(key_params: Dict[str, Any]) -> JSONValue:
        return handler(**key_params)

    return h


class TaskManager:
    input_cache: Redis
    output_cache: Redis
    input_expire: int
    sleep_interval: float

    def __init__(self, input_cache: Redis, output_cache: Redis,
                 input_expire: int = 60, sleep_interval: float = 1.):
        self.input_cache = input_cache
        self.output_cache = output_cache
        self.input_expire = input_expire
        self.sleep_interval = sleep_interval

    def process_tasks_star(self, handlers: Dict[str, Callable[..., JSONValue]]):
        return self.process_tasks(dict(
            (key_type, _star_wrap(handler))
            for (key_type, handler)
            in handlers.items()
        ))

    def process_tasks(self, handlers: Dict[str, Callable[[Dict[str, Any]], JSONValue]]):
        while True:
            try:
                key = self.input_cache.randomkey()
                if key is not None:
                    (key_type, key_params) = parse_key(key)
                    logging.debug(f'Popped task with key type {key_type}.')
                    handler = handlers.get(key_type)
                    if handler is not None:
                        logging.debug('Running task handler...')
                        value = handler(key_params)
                        logging.debug('Storing task result in output cache.')
                        self.output_cache.set(key, json.dumps(value))
                        self.input_cache.delete(key)
                    else:
                        raise Exception(
                            f'Sampled key has unrecognized type {key_type}')

                else:
                    sleep(self.sleep_interval)

            except Exception:
                logging.exception('Caught exception while handling task')

    def submit_task(self, key_type: str, key_params: Dict[str, Any]) -> TaskStatus:
        key = format_key(key_type, key_params)
        value_str = self.output_cache.get(key)
        if value_str is not None:
            load = self.input_cache.dbsize()
            return TaskStatus(
                done=True,
                value=json.loads(value_str),
                load=load,
            )
        else:
            self._update_input_key(key_type, key)
            load = self.input_cache.dbsize()
            return TaskStatus(
                done=False,
                value=None,
                load=load,
            )

    def _update_input_key(self, key_type: str, key: str):
        self.input_cache.set(key, '1', ex=self.input_expire)


class DistributedTaskManager(TaskManager):
    lock: Optional[Lock]

    def __init__(self, input_cache: Redis, output_cache: Redis,
                 input_expire: int = 60, lock: Optional[Lock] = None):
        super().__init__(input_cache, output_cache,
                         input_expire=input_expire, sleep_interval=0)
        self.lock = lock

    def process_tasks(self, handlers: Dict[str, Callable[[Dict[str, Any]], JSONValue]]):
        key_types = list(handlers.keys())

        while True:
            try:
                logging.debug(f'Expiring items older than {self.input_expire} seconds...')
                time = self._get_time()
                for key_type in key_types:
                    self.input_cache.zremrangebyscore(key_type, 0, time - self.input_expire)

                logging.debug(f'Popping new task from {key_types}...')
                pop_result = self.input_cache.bzpopmax(key_types)
                if pop_result is not None:
                    (key_type_bytes, key, score) = pop_result
                    key_type = key_type_bytes.decode('utf-8')
                    logging.debug(f'Popped task with key type {key_type}.')
                    key_params = parse_key(key)[1]
                    handler = handlers[key_type]

                    if self.lock is not None:
                        logging.debug('Acquiring lock...')
                        with self.lock:
                            logging.debug('Lock acquired; running task handler...')
                            value = handler(key_params)

                            # Store output within lock context in case the lock has already been
                            # released:  Exiting the context will raise an exception, but we still
                            # successfully computed the task output and don't want to waste it.
                            logging.debug('Storing task result in output cache.')
                            self.output_cache.set(key, json.dumps(value))

                    else:
                        logging.debug('Running task handler...')
                        value = handler(key_params)

                        logging.debug('Storing task result in output cache.')
                        self.output_cache.set(key, json.dumps(value))

                else:
                    raise Exception('Failed to pop new task.')

            except LockNotOwnedError:
                logging.warning('Lock has new owner; could not release.')

            except LockError as ex:
                raise ex

            except Exception:
                logging.exception('Caught exception while handling task')

    def _update_input_key(self, key_type: str, key: str):
        self.input_cache.zadd(key_type, {key: self._get_time()})

    def _get_time(self) -> int:
        return self.input_cache.time()[0]
