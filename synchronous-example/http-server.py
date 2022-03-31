#!/usr/bin/env python3

import logging
from typing import Any, Dict

from flask import Flask, jsonify, request
from waitress import serve

from factorization import factorize


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


def create_app():
    app = Flask(__name__)
    worker = Worker()

    @app.route('/factorize', methods=['POST'])
    # If you want to access the API from a web page served from another
    # server, add the flask-cors package to requirements.txt, add
    # "from flask_cors import cross_origin" to the imports, and
    # uncomment the following decorator:
    # @cross_origin()
    def factorize():
        input_data = request.json
        output_data = worker.do_task(input_data['number'])
        return jsonify(output_data)

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
    parser.add_argument('--log-level',
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        default='INFO',
                        help='Minimum severity level of log messages to show')
    args = parser.parse_args()

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        level=args.log_level)

    app = create_app()
    serve(app, host=args.host, port=args.port, threads=1)


if __name__ == '__main__':
    main()
