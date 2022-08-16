import os
import base64


def send_generic_file(fpath):
    '''
    Fetch and return a file given by fpath
    '''

    if not os.path.isfile(fpath):
        return {
            'statusCode': 200,
            'body': f"{fpath} missing from evaluation function files",
            'headers': {
                'Content-Type': 'application/octet-stream',
            },
            'isBase64Encoded': False
        }

    # Read file
    with open(fpath, 'rb') as file:
        docs_file = file.read()

    docs_encoded = base64.encodestring(docs_file)

    return {
        'statusCode': 200,
        'body': docs_encoded.decode(),
        'headers': {
            'Content-Type': 'application/octet-stream',
        },
        'isBase64Encoded': True
    }


def send_user_docs():
    """ 
    Return the user (teacher) documentation for this function
    """

    return send_generic_file('app/docs/user.md')


def send_dev_docs():
    """ 
    Return the developer (teacher) documentation for this function
    """

    return send_generic_file('app/docs/dev.md')
