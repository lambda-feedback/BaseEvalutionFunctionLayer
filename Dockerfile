# Base image is Python 3.8 provided by AWS Lambda in Docker Hub
FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app

# These are visible, the image is public so secrets would be accessible anyways
# We'd like these to be available if any evaluation function needs it...
# TODO: Find a better way to do thi
ARG INVOKER_ID
ARG INVOKER_KEY
ARG INVOKER_REGION

ENV INVOKER_ID=${INVOKER_ID}\
  INVOKER_KEY=${INVOKER_KEY}\
  INVOKER_REGION=${INVOKER_REGION}

# Install backend dependencies
COPY requirements.txt base_requirements.txt
RUN pip3 install -r base_requirements.txt

# Copy the scripts
COPY __init__.py ./app/
COPY handler.py ./app/
COPY tests/*.py ./app/tests/
COPY tools/*.py ./app/tools/

# Keep these in for backwards compatibility
ENV REQUEST_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/request.json
ENV RESPONSE_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/responsev2.json

# New schemas for evaluation function.
ENV EVAL_REQUEST_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/request/eval.json
ENV PREVIEW_REQUEST_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/request/preview.json

ENV EVAL_RESPONSE_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/response/eval.json
ENV HEALTH_RESPONSE_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/response/healthcheck.json
ENV PREVIEW_RESPONSE_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/response/preview.json