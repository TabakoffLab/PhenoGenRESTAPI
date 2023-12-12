import os, json, pymysql
import boto3,MyDBConnection, SharedUtilityFunctions

logger=None
functionPath="genes/gene"


def genericReport(report):
  print("genericReport")


def snpReport(report):
  print("snpReport")


def transcriptReport(report):
  print("transcriptReport")


def getHelp():
  response=SharedUtilityFunctions.getHelpMain()
  response['parameters'][
    'gene'] = "Gene parameter - Required - This parameter is required to pull up a gene report.  This should correspond to the ensembl ID or PhenoGen ID of the gene."
  response['parameters'][
    'report'] = "Report parameter - This parameter specifies the type of report returned.  Options: generic,snp,transcript"
  return response


def ensemblClient(request):
  response = {}
  
  return response


def lambda_handler(event, context):
  logger = SharedUtilityFunctions.setupLog()
  ip = event['context']['source-ip']
  SharedUtilityFunctions.sendSQSMessage(functionPath, ip)
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
        return SharedUtilityFunctions.respond(SharedUtilityFunctions.InputError('gene', 'Gene parameter is required'))
      if ('report' in payload):
        report = payload['report']
      report = {"payload": payload}
      genericReport(report)
      if (report == "SNP"):
        snpReport(report)
      elif (report == "Transcript"):
        transcriptReport(report)
      return SharedUtilityFunctions.respond(None, report)
    else:
      return SharedUtilityFunctions.respond(None, getHelp())
  else:
    return SharedUtilityFunctions.respond(SharedUtilityFunctions.InputError('HTTPMethod', 'Unsupported method ' + format(operation)))

