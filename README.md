# BaseEvalutionFunctionLayer
Base docker image for evaluation functions coded in python. This layer cannot function alone, it needs to be extended in a specific way by evaluation function it supports. 

This layer encompases all the behaviour that is universal to all evaluation functions: 
- Request and response schema validation
- Unit testing setup
- Function commands:
  - `grade`: calls the function in the user-defined `grading.py` file
  - `healthcheck`: runs all unittests for schema testing as well as user-defined tests in `grading_tests.py`.
  - `docs`: returns the `docs.md` user-defined file. 

*Note: user-defined files are those provided by the evaluation function code meant to extend this layer*