import os, json, pymysql
import boto3,MyDBConnection


def respond(err, res=None):
  body = ""
  if err:
    if (res is not None):
      body = {"message": err.message, "help": json.dumps(res)}
    else:
      body = {"message": err.message}
  else:
    body = json.dumps(res)
  return {
    'statusCode': '400' if err else '200',
    'body': body,
    'headers': {
      'Content-Type': 'application/json',
    },
    'isBase64Encoded': False
  }


def genericReport(report):
  print("genericReport")


def snpReport(report):
  print("snpReport")


def transcriptReport(report):
  print("transcriptReport")


def getHelp():
  response = {}
  response['parameters'] = {}
  response['parameters'][
    'gene'] = "Gene parameter - Required - This parameter is required to pull up a gene report.  This should correspond to the ensembl ID or PhenoGen ID of the gene."
  response['parameters'][
    'report'] = "Report parameter - This parameter specifies the type of report returned.  Options: generic,snp,transcript"
  return response


def ensemblClient(request):
  response = {}
  
  return response


def lambda_handler(event, context):
  operation = 'GET'
  if('httpMethod' in event):
    operation=event['httpMethod']
  geneID = ""
  report = "generic"
  if operation == 'GET':
    payload=None
    if('querystring' in event['params']):
      payload = event['params']['querystring']
    if (payload != None and payload != ""):
      if ('gene' in payload):
        geneID = payload['gene']
      else:
        return respond(InputError('gene', 'Gene parameter is required'))
      if ('report' in payload):
        report = payload['report']
      report = {"payload": payload}
      genericReport(report)
      if (report == "SNP"):
        snpReport(report)
      elif (report == "Transcript"):
        transcriptReport(report)
      return respond(None, report)
    else:
      return respond(None, getHelp())
  else:
    return respond(InputError('HTTPMethod', 'Unsupported method ' + format(operation)))


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