# Base image is Python 3.8 provided by AWS Lambda in Docker Hub
FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app

# Install backend dependencies
COPY requirements.txt base_requirements.txt
RUN pip3 install -r base_requirements.txt

# Copy the scripts
COPY __init__.py ./app/
COPY handler.py ./app/
COPY tests/*.py ./app/tests/
COPY tools/*.py ./app/tools/

ENV REQUEST_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/request.json
ENV RESPONSE_SCHEMA_URL https://raw.githubusercontent.com/lambda-feedback/request-response-schemas/master/responsev2.json