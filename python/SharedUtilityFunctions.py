import logging,json,boto3
from datetime import datetime

def setup(event,functionPath,operation):
    ip = '0.0.0.0'
    logger = setupLog()
    logger.info(event)
    if 'context' in event:
        ip = event['context']['source-ip']
    sendSQSMessage(functionPath, ip)

    if ('httpMethod' in event):
        operation = event['httpMethod']
    return (logger,operation)

def setupLog():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    return logger

def respond(err, res=None):
    body=""
    if err :
        if(res is not None):
            body={"message":err.message,"help": json.dumps(res)}
        else:
            body = {"message": err.message }
    else:
        body=res #json.dumps(res)
    return {
        'statusCode': err.errCode if err else '200',
        'body': body,
        'headers': {
            'Content-Type': 'application/json',
        },
        'isBase64Encoded': False
    }

def formatResponse(message,datasets):
    results = {
        "message": message,
        "parameters": {
            "ResultCount": len(datasets)
        },
        "data": datasets}
    return results

def getHelpMain():
    response={"methods" : "GET",
                "parameters":{}
              }
    return response


def sendSQSMessage(pathCall,IP):
    queue_url = "https://sqs.us-west-2.amazonaws.com/325177137737/RESTAPICallLogging"
    success=False
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("pathCall:"+pathCall+"::"+IP+"::"+dt_string)
    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=pathCall,
        DelaySeconds=0,
        MessageAttributes={
            'IP': {
                'DataType': 'String',
                'StringValue': IP
            },
            'DATE': {
                'DataType': 'String',
                'StringValue': dt_string
            }
        }
    )
    print(response['MessageId'])
    success=True
    return success

class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

      Attributes:
          expression -- input expression in which the error occurred
          message -- explanation of the error
      """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
        self.errCode = 400


class ParameterMissingError(Error):
    """Exception raised for errors in the input.

      Attributes:
          expression -- input expression in which the error occurred
          message -- explanation of the error
      """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
        self.errCode = 422



#365473
#1F354F