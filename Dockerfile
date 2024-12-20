ARG PYTHON_VERSION

# Base image is Python 3.8/3.9/3.10/3.11/3.12 provided by AWS Lambda in Docker Hub
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

WORKDIR /app

# These are visible, the image is public so secrets would be accessible anyways
# We'd like these to be available if any evaluation function needs it...
# TODO: ~Find a better way to do this~
# TODO: We can probably use docker secrets, let's see...
ARG INVOKER_ID
ARG INVOKER_KEY
ARG INVOKER_REGION

ENV INVOKER_ID=${INVOKER_ID}
ENV INVOKER_KEY=${INVOKER_KEY}
ENV INVOKER_REGION=${INVOKER_REGION}

# Install backend dependencies
COPY requirements.txt base_requirements.txt
RUN pip3 install -r base_requirements.txt

# Copy the scripts
COPY __init__.py ./app/
COPY handler.py ./app/
COPY tests/*.py ./app/tests/
COPY tools/*.py ./app/tools/
COPY schemas/ ./app/schemas/

ENV SCHEMA_DIR=/app/app/schemas/
