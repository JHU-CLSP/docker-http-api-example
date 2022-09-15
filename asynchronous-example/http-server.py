#!/usr/bin/env python3

import json
import logging
from hashlib import sha256
from typing import Any, Dict

from flask import Flask, jsonify, request
from redis import Redis
from rq import Queue  # type: ignore
from waitress import serve

from cached_factorization import cached_factorize


# Default time-to-live (in seconds) of jobs in queue.
# We set this to a small number, assuming active jobs will be
# polled (checked & resubmitted) relatively frequently.
DEFAULT_TTL = 5


def format_key(key_namespace: str, key_params: Dict[str, Any]) -> str:
    '''
    Create a unique redis key with given namespace and params.

    Use the key naming convention of namespace:hash to avoid collisions
    with Redis Queue and other systems.
    '''
    key_params_json_bytes = json.dumps(sorted(key_params.items())).encode('ascii')
    return f'{key_namespace}:{sha256(key_params_json_bytes).hexdigest()}'


def create_app(queue: Queue, cache_url: str, ttl: int = DEFAULT_TTL):
    cache = Redis.from_url(cache_url)
    app = Flask(__name__)

    @app.route('/factorize', methods=['POST'])
    # If you want to access the API from a web page served from another
    # server, add the flask-cors package to requirements.txt, add
    # "from flask_cors import cross_origin" to the imports, and
    # uncomment the following decorator:
    # @cross_origin()
    def factorize():
        # Compute task parameters from HTTP parameters
        data = request.json

        # Submit task
        number = data['number']
        cache_key = format_key('factorize', {'n': number})
        cache_result = cache.get(cache_key)
        if cache_result is not None:
            factorization = json.loads(cache_result)
            return jsonify({
                'done': True,
                'number': number,
                'factorization': factorization,
                'factorization_str': ' '.join(f'{b}^{e}' for (b, e) in sorted(factorization)),
            })
        else:
            queue.enqueue(
                cached_factorize, number, cache_key, cache_url,
                ttl=ttl)
            return jsonify({
                'done': False,
                'number': number,
                'factorization': None,
                'factorization_str': None,
            })

    return app


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        description='Launch HTTP server providing JSON API for example factorization task.',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Hostname/IP to listen on.')
    parser.add_argument('--port', type=int, default=8080,
                        help='TCP port to listen on.')
    parser.add_argument('--queue-url', type=str, default='redis://localhost',
                        help='Redis queue URL.')
    parser.add_argument('--cache-url', type=str, default='redis://localhost',
                        help='Redis cache URL.')
    parser.add_argument('--ttl', type=int, default=DEFAULT_TTL,
                        help='Time-to-live (in seconds) of jobs in queue before they are expired.')
    parser.add_argument('--threads', type=int, default=1,
                        help='Number of threads to use for HTTP server.')
    parser.add_argument('--log-level',
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        default='INFO',
                        help='Minimum severity level of log messages to show')
    args = parser.parse_args()

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        level=args.log_level)

    queue = Queue(connection=Redis.from_url(args.queue_url))
    app = create_app(queue, args.cache_url, ttl=args.ttl)
    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == '__main__':
    main()
