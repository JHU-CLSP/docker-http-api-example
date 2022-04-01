# Docker HTTP API Example

Example code for creating an HTTP API for an ML model (or similar) in
Docker.  If you have a model or other system that takes a long time to
start up and you want to send requests to it online (not all at once),
use this code to create a Docker container providing an HTTP API for
that system.

Two examples are provided: one for synchronous processing and one for
asynchronous processing.  The asynchronous example is more complex but
more robust to long-running tasks.  If your tasks take more than a
few seconds to complete, I suggest using an asynchronous approach.

The task handlers process one task at a time.  However, in the
asynchronous example, parallel processing can be performed by creating
multiple instances of the handler container.

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
request to the server.  Install the Python `requests` package (using
`pip`) if you don't already have it, open a Python console, and do:

```python
import requests
requests.post('http://localhost:8123/factorize', json={'number': 408216}).json()
```

The last command should return a parsed response like:

```python
{'factorization': [[2, 3], [3, 1], [73, 1], [233, 1]],
 'factorization_str': '2^3 3^1 73^1 233^1',
 'number': 408216}
```

## Asynchronous Processing

In this example, the HTTP request handler checks a redis database for a
cached result, returns the result if it is found, and otherwise adds
the input parameters to a second redis database and returns a null
result.  The handler is designed to be polled, such that the consumer
of the API calls it every so many seconds until a result is returned.

The code in this example processes tasks in a random order.  Although
it would be more intuitive and just as easy to implement an approach
that processes tasks in the order they are received, the randomized
approach offers several advantages.  First, the availability/expected
wait time is the same for all tasks, so if a client submits a large
number of inputs to process and then another client connects and
submits its own inputs, the second client doesn't have to wait until
the first client's tasks are all done to start getting results.
Second, inputs are automatically expired after a pre-specified amount
of time using the built-in time-to-live functionality of redis keys.
This allows us to more gracefully handle clients connecting, submitting
a large number of inputs to process, and disconnecting (perhaps the
user closed the browser window or experienced an interruption in
internet access).

These features are helpful in my use cases so far, but if you have
different requirements, you may want to modify the code to process
tasks in order.  If that is the case, I suggest using a redis list
data type to store inputs (instead of storing each input in its own
key), using LPUSH to submit inputs and BRPOP to receive them.  An
advantage of this approach is that BRPOP blocks until there are
elements to read from the list, so we don't have to poll the database
when it is empty.

### Usage

First, change directory to `asynchronous-example`.

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

```python
import requests
requests.post('http://localhost:8123/factorize', json={'number': 408216}).json()
```

The last command should return a parsed response like:

```python
{'done': False,
 'factorization': None,
 'factorization_str': None,
 'load': 1,
 'number': 408216}
```

This status indicates the task is not yet complete.  Re-run the command
until the task is complete.  When it is complete, you should get a
response like:

```python
{'done': True,
 'factorization': [[2, 3], [3, 1], [73, 1], [233, 1]],
 'factorization_str': '2^3 3^1 73^1 233^1',
 'load': 0,
 'number': 408216}
```

A complete example that submits twenty numbers to be factorized and
polls the server until they are done, printing the current status every
second:

```python
import random
import requests
import time

done = False
numbers = [random.randint(2, 2**20) for _ in range(20)]
while not done:
    done = True
    for n in numbers:
        status = requests.post(
            'http://localhost:8123/factorize', json={'number': n}
        ).json()

        if status['done']:
            print(f'{n:7d} =', status['factorization_str'])
        else:
            print(f'{n:7d} = ...')

        done = done and status['done']

    if not done:
        print()
        time.sleep(1)
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

#### Note on Input and Output Size

Redis keys and values have a maximum size of 512 MB.  If your
task inputs or outputs reach that threshold when encoded as JSON, you
will need to take a different approach.
