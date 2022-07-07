# BaseEvalutionFunctionLayer
Base docker image for evaluation functions coded in python. This layer cannot function alone, it needs to be extended in a specific way by evaluation function it supports. 

This layer encompases all the behaviour that is universal to all evaluation functions: 
- Request and response schema validation
- Unit testing setup
- Function commands:
  - `eval`: calls the function in the user-defined `evaluation.py` file
  - `healthcheck`: runs all unittests for schema testing as well as user-defined tests in `evaluation_tests.py`.
  - `docs`: returns the `docs.md` user-defined file. 

*Note: user-defined files are those provided by the evaluation function code meant to extend this layer*

## Behaviour and Usage
Commands as passed in 'command' header from each request. By default (if not header is present), the function will run the `eval` command. 

## Requirements from the superseding layer
This function makes references to files and functions which don't exist yet in this layer - those need to be provided by the superseding layer. They're shown here in the way a dockerfile might be extending it.

```dockerfile
FROM ###THIS IMAGE###

WORKDIR /app

# Install requirements if your evaluation function needs them
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the evaluation and testing scripts
COPY evaluation.py ./app/
COPY evaluation_tests.py ./app/

# Copy Documentation
COPY docs.md ./app/

# Set permissions so files and directories can be accessed on AWS
RUN chmod 644 $(find . -type f)
RUN chmod 755 $(find . -type d)

# The entrypoint for AWS is to invoke the handler function within the app package
CMD [ "/app/app.handler" ]
```


### Operating Container Structure
Since this is only just a base layer for eval functions, the repo's file structure won't match the file structure inside the built image, which can get confusing at times. This is what the `/app/` directory (where all our data is contained) will look like for an operational function:

```
|____requirements.txt
|____base_requirements.txt
|____app
   |______init__.py
   |____tests
   |  |______init__.py
   |  |____requests.py
   |  |____responses.py
   |  |____handling.py
   |____tools
   |  |______init__.py
   |  |____validate.py
   |  |____docs.py
   |  |____parse.py
   |  |____healthcheck.py
   |____docs.md
   |____handler.py
   |____evaluation_tests.py
   |____evaluation.py
```


## Dev Notes
Can run the following command to look around the container of a running function

```bash
docker exec -it eval-function bash
```

From a container which exposes port 8080 to the real port 9000, requests can be made to the function using the url:

```
http://localhost:9000/2015-03-31/functions/function/invocations
```


