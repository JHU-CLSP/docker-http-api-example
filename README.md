# Docker HTTP API Example

Example code for creating an HTTP API for an ML model (or similar) in
Docker.  If you have a model or other system that takes a long time to
start up and you want to send requests to it online (not all at once),
use this code to create a Docker container providing an HTTP API for
that system.

## Usage

Build the Docker image with the following command:

```
docker build -t docker-http-api-example .
```

Then start a container from that image:

```
docker run -it -p 8123:8080 docker-http-api-example
```

where 8123 is just some open TCP port on your system.  The HTTP
server listens on port 8080 inside the container, and Docker maps
that to port 8123 on your host system.

Then, in another terminal tab/window, do the following to send a
request to the server.  Install the Python `requests` package (using
`pip`) if you don't already have it, open a Python console, and do:

```python
import requests
requests.post('http://localhost:8123/ask', json={'question': 'Will I?'}).json()
```

The last command should return a parsed response like:

```python
{'answer': 'Maybe.', 'confidence': 1.0}
```
