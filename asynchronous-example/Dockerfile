FROM continuumio/miniconda3:4.10.3

# Install build tools (needed by some Python packages) and clear cache
RUN apt-get update \
    && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies before adding all files
# (we don't want to have to re-install dependencies every time the code
# changes)
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ADD . /app
