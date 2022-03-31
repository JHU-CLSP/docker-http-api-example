#!/usr/bin/env python3

import logging

from flask import Flask, jsonify, request
from redis import Redis
from waitress import serve

from redis_tasks import TaskManager


def create_app(task_manager: TaskManager):
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
        key_type = 'factorization'
        key_params = {'number': data['number']}

        # Submit task
        status = task_manager.submit_task(key_type, key_params)

        if status.done:
            # Task is done: return done status with result
            return jsonify({
                'done': True,
                'number': data['number'],
                'factorization': status.value['factorization'],
                'factorization_str': status.value['factorization_str'],
                'load': status.load
            })
        else:
            # Task is not done: return in-progress status
            return jsonify({
                'done': False,
                'number': data['number'],
                'factorization': None,
                'factorization_str': None,
                'load': status.load
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
    parser.add_argument('--redis-host', type=str, default='localhost',
                        help='Redis cache host.')
    parser.add_argument('--redis-port', type=int, default=6379,
                        help='Redis cache port')
    parser.add_argument('--output-cache-db', type=int, default=0,
                        help='Redis output cache DB number')
    parser.add_argument('--input-cache-db', type=int, default=1,
                        help='Redis input cache DB number')
    parser.add_argument('--sleep-interval', type=int, default=1,
                        help='Number of seconds to sleep after finding cache is empty')
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

    input_cache = Redis(host=args.redis_host, port=args.redis_port, db=args.input_cache_db)
    output_cache = Redis(host=args.redis_host, port=args.redis_port, db=args.output_cache_db)
    task_manager = TaskManager(input_cache, output_cache)
    app = create_app(task_manager)
    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == '__main__':
    main()
