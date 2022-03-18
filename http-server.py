#!/usr/bin/env python3

import logging

from flask import Flask, jsonify, request
from waitress import serve


class Predictor:
    def __init__(self):
        logging.info('Initializing...')
        logging.info('Done.')

    def predict(self, data):
        question = data['question']  # noqa

        # Do the heavy lifting here
        logging.info('Predicting...')
        answer = 'Maybe.'
        confidence = 1.
        logging.info('Done.')

        return {'answer': answer, 'confidence': confidence}


def create_app():
    app = Flask(__name__)
    predictor = Predictor()

    @app.route('/ask', methods=['POST'])
    # If you want to access the API from a web page served from another
    # server, add the flask-cors package to requirements.txt, add
    # "from flask_cors import cross_origin" to the imports, and
    # uncomment the following decorator:
    # @cross_origin()
    def ask():
        question_data = request.json
        answer_data = predictor.predict(question_data)
        return jsonify(answer_data)

    return app


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        description='Launch HTTP server providing JSON API for question answering model.',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Hostname/IP to listen on.')
    parser.add_argument('--port', type=int, default=8080,
                        help='TCP port to listen on.')
    parser.add_argument('--threads', type=int, default=1,
                        help='Number of threads to use for HTTP server.')
    args = parser.parse_args()

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        level=logging.INFO)

    app = create_app()
    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == '__main__':
    main()
