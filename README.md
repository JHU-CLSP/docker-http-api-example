# Docker HTTP API Example

Example code for creating an HTTP API for an ML model (or similar) in
Docker.  If you have a model or other system that takes a long time to
start up and you want to send requests to it online (not all at once),
use this code to create a Docker container providing an HTTP API for
that system.

Two examples are provided: one for synchronous processing and one for
asynchronous processing.  The asynchronous example is more complex but
may work better when each prediction (or other background task)
takes a long time to finish.

The task handlers process one task at a time.  However, in the
asynchronous example, parallel processing can be performed by creating
multiple instances of the worker container.

Feedback is welcome!

## Synchronous Processing

In this example, the tasks are performed directly by the HTTP request
handler.  Accordingly, they are completed in the order they are
received.

### Usage

First, change directory to `synchronous-example`.

Build the Docker image with the following command:

```
docker build -t sync-example .
```

Then start a container from that image:

```
docker run -it -p 8123:8080 sync-example
```

where 8123 is just some open TCP port on your system.  The HTTP
server listens on port 8080 inside the container, and Docker maps
that to port 8123 on your host system.

Then, in another terminal tab/window, do the following to send a
request to the server:

```bash
curl http://localhost:8123/factorize -H 'Content-Type: application/json' -d '{"number": 408216}'
```

This command should return a response like:

```json
{"factorization":[[2,3],[3,1],[73,1],[233,1]],"factorization_str":"2^3 3^1 73^1 233^1","number":408216}
```

## Asynchronous Processing

In this example, the HTTP request handler checks a redis database for a
cached result, returns the result if it is found, and otherwise adds
the task to a queue in a second database and returns a null result.
The handler is designed to be polled, such that the consumer
of the API calls it every second (for example) until a result is
returned.

### Usage

First, change the current directory to `asynchronous-example`.

This example builds on the synchronous example.  In the synchronous
example, we first built the Docker image and then started a container
from that image in the next step.  In this example, we use Docker
Compose to create several containers, automatically building the
requisite image in the process:

```bash
docker-compose up
```

The Docker Compose configuration file, `docker-compose.yml`, specifies
which containers are created and how.  Included in this configuration
is a port mapping from 8123 on the host to 8080 in the container.  If
port 8123 is in use on your host, you may need to change the host port
in the configuration.

We can now access HTTP server as before.  In another terminal
tab/window, do the following to send a request.  Install the Python
`requests` package (using `pip`) if you don't already have it, open a
Python console, and do:

```bash
curl http://localhost:8123/factorize -H 'Content-Type: application/json' -d '{"number": 408216}'
```

This command should return a parsed response like:

```json
{"done":false,"factorization":null,"factorization_str":null,"number":408216}
```

This status indicates the task is not yet complete.  Re-run the command
until the task is complete.  When it is complete, you should get a full
response like in the synchronous example:

```json
{"done":true,"factorization":[[2,3],[3,1],[73,1],[233,1]],"factorization_str":"2^3 3^1 73^1 233^1","number":408216}
```

The `polling-client.py` script allows you to simulate parallel requests
by submitting twenty large numbers to be factorized and polling the
server until they are done.  To use it, do:

```
python polling-client.py http://localhost:8123/factorize
```

#### Parallel Processing

Parallel processing can be achieved by running multiple instances of
the worker using the `--scale` flag to `docker-compose`:

```
docker-compose up --scale worker=4
```

#### Note on Building Images with Docker Compose

If you run Docker Compose multiple times, it will only rebuild the
images under certain conditions.  To rebuild the images every time, do:

```
docker-compose up --build
```

Run `docker-compose help up` for more information.

#### Note on Input and Output Size

Redis keys and values have a maximum size of 512 MB.  If your
task inputs or outputs reach that threshold when encoded as JSON, you
will need to take a different approach.
