#!/usr/bin/env python3

import logging
from typing import Any, Dict

from redis import Redis

from factorization import factorize
from redis_tasks import TaskManager


class Worker:
    def __init__(self):
        logging.info('Initializing...')
        logging.info('Done.')

    def do_task(self, number: int) -> Dict[str, Any]:
        # Do the heavy lifting here
        logging.info(f'Finding prime factorization of {number}...')
        factorization = factorize(number)
        logging.info('Done.')

        return {
            'number': number,
            'factorization': factorization,
            'factorization_str': ' '.join(f'{b}^{e}' for (b, e) in sorted(factorization))
        }


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        description='Run background worker doing factorization task for HTTP JSON API.',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Hostname/IP to listen on.')
    parser.add_argument('--port', type=int, default=8080,
                        help='TCP port to listen on.')
    parser.add_argument('--redis-host', type=str, default='localhost',
                        help='Redis cache host.')
    parser.add_argument('--redis-port', type=int, default=6379,
                        help='Redis cache port')
    parser.add_argument('--output-cache-db', type=int, default=0,
                        help='Redis output cache DB number')
    parser.add_argument('--input-cache-db', type=int, default=1,
                        help='Redis input cache DB number')
    parser.add_argument('--sleep-interval', type=int, default=1,
                        help='Number of seconds to sleep after finding input cache is empty')
    parser.add_argument('--log-level',
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        default='INFO',
                        help='Minimum severity level of log messages to show')
    args = parser.parse_args()

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        level=args.log_level)

    input_cache = Redis(host=args.redis_host, port=args.redis_port, db=args.input_cache_db)
    output_cache = Redis(host=args.redis_host, port=args.redis_port, db=args.output_cache_db)
    task_manager = TaskManager(input_cache, output_cache)
    worker = Worker()
    task_manager.process_tasks_star({'factorization': worker.do_task})


if __name__ == '__main__':
    main()
