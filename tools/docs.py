import os 
import base64

def send_docs_file():
    '''
    Fetch and return the docs.md file relevant to this function
    '''

    docs_path = "app/docs.md"

    # Read docs file 
    with open(docs_path, 'rb') as file:
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